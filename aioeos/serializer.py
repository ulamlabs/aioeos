from abc import ABC, abstractmethod
from datetime import datetime, timezone
import inspect
import struct
from typing import Any, List, Tuple, Type, Union

from aioeos import types, exceptions


class BaseSerializer(ABC):
    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        """Returns byte-encoded value"""
        pass  # pragma: no cover

    @abstractmethod
    def deserialize(self, value: bytes) -> Tuple[int, Any]:
        """
        Returns a tuple containing length of original data and deserialized
        value
        """
        pass  # pragma: no cover


class BasicTypeSerializer(BaseSerializer):
    """
    Serializes basic types such as integers and floats using ``struct`` module

    :params fmt: format string, please refer to documentation for `struct
                 module <https://docs.python.org/3/library/struct.html>`_
    """

    def __init__(self, fmt: Union[bytes, str] = ''):
        assert fmt, 'provide valid fmt value'
        self.fmt = fmt

    def serialize(self, value: Any) -> bytes:
        return struct.pack(self.fmt, value)

    def deserialize(self, value: bytes) -> Tuple[int, Any]:
        length = struct.calcsize(self.fmt)
        values = struct.unpack_from(self.fmt, value)
        return length, values[0]


class AbiNameSerializer(BasicTypeSerializer):
    """
    Serializer for ABI names. ABI names can only contain these characters:
    ``.12345abcdefghijklmnopqrstuvwxyz``. Maximum length is 13 chars.
    """

    def __init__(self):
        self.alphabet = '.12345abcdefghijklmnopqrstuvwxyz'
        self.fmt = 'Q'

    def serialize(self, value: str) -> bytes:
        # Run preliminary checks
        if len(value) > 13:
            raise exceptions.EosSerializerAbiNameTooLongException

        if any(x not in self.alphabet for x in value):
            raise exceptions.EosSerializerAbiNameInvalidCharactersException

        name = sum(
            (self.alphabet.index(char) & 0x1F) << (64-5 * (index + 1))
            for index, char in enumerate(value[:12])
        )
        if len(value) > 12:
            name |= self.alphabet.index(value[12]) & 0x0F
        return super().serialize(name)

    def deserialize(self, value: bytes) -> Tuple[int, str]:
        length, decoded_value = super().deserialize(value)
        name = ['.'] * 13
        i = 12
        while i >= 0:
            # 13th character is encoded on last 2 bytes
            mask = 0x0F if i == 12 else 0x1F
            name[i] = self.alphabet[decoded_value & mask]
            decoded_value >>= 4 if i == 12 else 5
            i -= 1
        return length, ''.join(name).rstrip('.')


class VarUIntSerializer(BaseSerializer):
    """
    Serializer for ABI VarUInt type. This type has different length based on
    how many bytes are required to encode given integer.
    """

    def serialize(self, value: int) -> bytes:
        # TODO: copied over from libeospy, I'm 99% sure this is overcomplicated
        array = bytearray()
        val = int(value)
        buf = int((val) & 0x7f)
        val >>= 7
        buf |= (val > 0) << 7
        array.append(int(buf))
        while val:
            buf = int((val) & 0x7f)
            val >>= 7
            buf |= (val > 0) << 7
            array.append(int(buf))
        return bytes(array)

    def deserialize(self, value: bytes) -> Tuple[int, int]:
        # TODO: copied over from libeospy, I'm 99% sure this is overcomplicated
        shift = 0
        result = 0
        cursor = 0
        while True:
            tmp = value[cursor]
            result |= (tmp & 0x7f) << shift
            shift += 7
            cursor += 1
            if not(tmp & 0x80):
                break
        return cursor, result


class AbiBytesSerializer(BaseSerializer):
    """
    Serializer for ABI bytes type. Serialized value consists of raw bytes
    prefixed with payload size encoded as VarUInt.
    """

    def serialize(self, value: bytes) -> bytes:
        assert isinstance(value, bytes), 'Provide binary format'
        prefix = VarUIntSerializer().serialize(len(value))
        return b''.join((prefix, value))

    def deserialize(self, value: bytes) -> Tuple[int, bytes]:
        prefix_length, prefix = VarUIntSerializer().deserialize(value)
        overall_length = prefix_length + prefix
        return overall_length, value[prefix_length:overall_length]


class AbiTimePointSerializer(BasicTypeSerializer):
    """
    Serializer for ABI TimePoint type. Encodes timestamp with milisecond
    precision.
    """

    def __init__(self):
        self.fmt = 'Q'

    def serialize(self, value: datetime) -> bytes:
        return super().serialize(int(value.timestamp() * 1000))

    def deserialize(self, value: bytes) -> Tuple[int, datetime]:
        length, decoded_value = super().deserialize(value)
        return (
            length, datetime.fromtimestamp(decoded_value / 1000, timezone.utc)
        )


class AbiTimePointSecSerializer(BasicTypeSerializer):
    """
    Serializer for ABI TimePointSec type. It's essentially a timestamp.
    """

    def __init__(self):
        self.fmt = 'I'

    def serialize(self, value: datetime) -> bytes:
        return super().serialize(int(value.timestamp()))

    def deserialize(self, value: bytes) -> Tuple[int, datetime]:
        length, decoded_value = super().deserialize(value)
        return length, datetime.fromtimestamp(decoded_value, timezone.utc)


class AbiStringSerializer(BaseSerializer):
    """
    Serializer for ABI String type. String format is similar to bytes as it's
    prefixed with length but it's comprised of ASCII codes for each character
    packed in binary format.
    """
    def serialize(self, value: str) -> bytes:
        return AbiBytesSerializer().serialize(value.encode())

    def deserialize(self, value: bytes) -> Tuple[int, str]:
        length, value = AbiBytesSerializer().deserialize(value)
        return length, value.decode()


class AbiObjectSerializer(BaseSerializer):
    def __init__(self, abi_class: Type):
        self.abi_class = abi_class

    def serialize(self, value: types.BaseAbiObject) -> bytes:
        assert issubclass(value.__class__, self.abi_class)
        return b''.join(
            serialize(
                getattr(value, field),
                value.__dataclass_fields__[field].type,
            )
            for field in value._serializable_fields()
        )

    def deserialize(self, value: bytes) -> Tuple[int, types.BaseAbiObject]:
        cursor = 0
        values = {}
        for field in self.abi_class._serializable_fields():
            length, values[field] = deserialize(
                value[cursor:],
                self.abi_class.__dataclass_fields__[field].type
            )
            cursor += length
        return cursor, self.abi_class(**values)


class AbiActionPayloadSerializer(BaseSerializer):
    def serialize(self, value: types.AbiActionPayload) -> bytes:
        assert not isinstance(value, dict), 'Convert data to ABI format first'
        if types.is_abi_object(type(value)):
            # mypy won't recognize that as a type check apparently
            serializer = AbiObjectSerializer(type(value))
            value = serializer.serialize(value)  # type: ignore
        assert isinstance(value, bytes)
        return AbiBytesSerializer().serialize(value)

    def deserialize(self, value: bytes) -> Tuple[int, bytes]:
        # TODO: figure out how to convert it back to BaseAbiObject or dict
        return AbiBytesSerializer().deserialize(value)


TYPE_MAPPING = {
    types.UInt8: BasicTypeSerializer('B'),
    types.UInt16: BasicTypeSerializer('H'),
    types.UInt32: BasicTypeSerializer('I'),
    types.UInt64: BasicTypeSerializer('Q'),
    types.Int8: BasicTypeSerializer('b'),
    types.Int16: BasicTypeSerializer('h'),
    types.Int32: BasicTypeSerializer('i'),
    types.Int64: BasicTypeSerializer('q'),
    types.Float32: BasicTypeSerializer('f'),
    types.Float64: BasicTypeSerializer('d'),
    types.Name: AbiNameSerializer(),
    types.VarUInt: VarUIntSerializer(),
    types.AbiBytes: AbiBytesSerializer(),
    types.AbiActionPayload: AbiActionPayloadSerializer(),  # type: ignore
    types.TimePoint: AbiTimePointSerializer(),
    types.TimePointSec: AbiTimePointSecSerializer(),
    str: AbiStringSerializer()
}


class AbiListSerializer(BaseSerializer):
    """
    Serializer for ABI List type. In binary format, it basically looks like
    this: ``[count][item 1][item 2]...``
    """

    def __init__(self, list_type: Type):
        self.eos_type = list_type.__args__[0]
        self.item_serializer = get_abi_type_serializer(self.eos_type)

    def serialize(self, value: List[Any]) -> bytes:
        return b''.join([
            VarUIntSerializer().serialize(len(value)),
            *(self.item_serializer.serialize(x) for x in value)
        ])

    def deserialize(self, value: bytes) -> Tuple[int, List[Any]]:
        # List always starts with a VarUInt representing item count
        prefix_length, count = VarUIntSerializer().deserialize(value)

        abi_bytes = value[prefix_length:]
        overall_length = prefix_length
        values = []

        for _ in range(count):
            # try to decode bytes as expected EOS type
            length, decoded_value = self.item_serializer.deserialize(abi_bytes)

            # advance buffer by read and decoded bytes
            overall_length += length
            abi_bytes = abi_bytes[length:]

            # append decoded value to values list
            values.append(decoded_value)
        return overall_length, values


def get_abi_type_serializer(abi_type: Type) -> BaseSerializer:
    if abi_type in TYPE_MAPPING:
        return TYPE_MAPPING[abi_type]
    elif getattr(abi_type, '_name', None) == 'List':
        return AbiListSerializer(abi_type)
    elif types.is_abi_object(abi_type):
        return AbiObjectSerializer(abi_type)

    # if type is not supported, raise an Exception
    raise exceptions.EosSerializerUnsupportedTypeException(abi_type)


def serialize(value: Any, abi_type: Type = None) -> bytes:
    """Serializes ABI values to binary format"""
    if not abi_type:
        is_class = inspect.isclass(value)
        abi_type = value.__class__ if is_class else type(value)
    return get_abi_type_serializer(abi_type).serialize(value)


def deserialize(value: bytes, abi_class: Type) -> Tuple[int, Any]:
    """Deserializes ABI values from binary format"""
    return get_abi_type_serializer(abi_class).deserialize(value)
