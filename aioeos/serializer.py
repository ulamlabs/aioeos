from datetime import datetime, timezone
import struct

from aioeos import types as eos_types
from aioeos.exceptions import EosSerializerUnsupportedTypeException


class BaseSerializer:
    def serialize(self, value):
        raise NotImplementedError

    def deserialize(self, value):
        raise NotImplementedError


class BasicTypeSerializer(BaseSerializer):
    def __init__(self, fmt=None):
        if fmt:
            self.fmt = fmt

    def serialize(self, value):
        return struct.pack(self.fmt, value)

    def deserialize(self, value):
        length = struct.calcsize(self.fmt)
        return length, struct.unpack_from(self.fmt, value)[0]


class AbiNameSerializer(BasicTypeSerializer):
    def __init__(self):
        self.alphabet = '.12345abcdefghijklmnopqrstuvwxyz'
        self.fmt = 'Q'

    def serialize(self, value):
        name = sum(
            (self.alphabet.index(char) & 0x1F) << (64-5 * (index + 1))
            for index, char in enumerate(value[:12])
        )
        if len(value) > 12:
            name |= self.alphabet.index(value[12]) & 0x0F
        return super().serialize(name)

    def deserialize(self, value):
        length, value = super().deserialize(value)
        name = ['.'] * 13
        i = 12
        while i >= 0:
            # 13th character is encoded on last 2 bytes
            name[i] = self.alphabet[value & (0x0F if i == 12 else 0x1F)]
            value >>= 4 if i == 12 else 5
            i -= 1
        return length, ''.join(name).rstrip('.')


class VarUIntSerializer(BaseSerializer):
    def serialize(self, value):
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
        return array

    def deserialize(self, value):
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


class AbiBytesSerializer(VarUIntSerializer):
    def serialize(self, value):
        # AbiBytes must be prefixed with length encoded as VarUInt
        prefix = super().serialize(len(value))
        return b''.join((prefix, value))

    def deserialize(self, value):
        prefix_length, prefix = super().deserialize(value)
        overall_length = prefix_length + prefix
        return overall_length, value[prefix_length:overall_length]


class AbiTimePointSerializer(BasicTypeSerializer):
    def __init__(self):
        self.fmt = 'Q'

    def serialize(self, value):
        return super().serialize(int(value.timestamp() * 1000))

    def deserialize(self, value):
        length, value = super().deserialize(value)
        return length, datetime.fromtimestamp(value / 1000, timezone.utc)


class AbiTimePointSecSerializer(BasicTypeSerializer):
    def __init__(self):
        self.fmt = 'I'

    def serialize(self, value):
        return super().serialize(int(value.timestamp()))

    def deserialize(self, value):
        length, value = super().deserialize(value)
        return length, datetime.fromtimestamp(value, timezone.utc)


class AbiStringSerializer(AbiBytesSerializer):
    """
    EOS String format is similar to bytes as it's prefixed with length
    and is comprised of ASCII codes for each character packed in binary
    format.
    """
    def serialize(self, value):
        return super().serialize(value.encode())

    def deserialize(self, value):
        length, value = super().deserialize(value)
        return length, value.decode()


TYPE_MAPPING = {
    eos_types.UInt8: BasicTypeSerializer('B'),
    eos_types.UInt16: BasicTypeSerializer('H'),
    eos_types.UInt32: BasicTypeSerializer('I'),
    eos_types.UInt64: BasicTypeSerializer('Q'),
    eos_types.Int8: BasicTypeSerializer('b'),
    eos_types.Int16: BasicTypeSerializer('h'),
    eos_types.Int32: BasicTypeSerializer('i'),
    eos_types.Int64: BasicTypeSerializer('q'),
    eos_types.Float32: BasicTypeSerializer('f'),
    eos_types.Float64: BasicTypeSerializer('d'),
    eos_types.Name: AbiNameSerializer(),
    eos_types.VarUInt: VarUIntSerializer(),
    eos_types.AbiBytes: AbiBytesSerializer(),
    eos_types.TimePoint: AbiTimePointSerializer(),
    eos_types.TimePointSec: AbiTimePointSecSerializer(),
    eos_types.String: AbiStringSerializer()
}


class AbiListSerializer(VarUIntSerializer):
    def __init__(self, list_type):
        self.eos_type = list_type.__args__[0]

    def serialize(self, value):
        prefix = super().serialize(len(value))
        return b''.join([
            prefix, *[encode_eos_type(self.eos_type, x) for x in value]
        ])

    def deserialize(self, value):
        # List always starts with a VarUInt representing item count
        prefix_length, count = super().deserialize(value)

        abi_bytes = value[prefix_length:]
        overall_length = prefix_length
        values = []

        for _ in range(count):
            # try to decode bytes as expected EOS type
            length, decoded_value = decode_eos_type(self.eos_type, abi_bytes)

            # advance buffer by read and decoded bytes
            overall_length += length
            abi_bytes = abi_bytes[length:]

            # append decoded value to values list
            values.append(decoded_value)
        return overall_length, values


def encode_eos_type(eos_type, value):
    # Use mapping to serialize basic type
    if eos_type in TYPE_MAPPING:
        return TYPE_MAPPING.get(eos_type).serialize(value)

    elif getattr(eos_type, '_name', None) == 'List':
        s = AbiListSerializer(eos_type)
        return s.serialize(value)
    elif isinstance(value, eos_types.BaseAbiObject):
        # if this is a basic ABI object, serialize it
        return serialize(value)

    # if type is not supported, raise an Exception
    raise EosSerializerUnsupportedTypeException(eos_type)


def decode_eos_type(eos_type, binary):
    # Use mapping to serialize basic type
    if eos_type in TYPE_MAPPING:
        return TYPE_MAPPING.get(eos_type).deserialize(binary)

    elif getattr(eos_type, '_name', None) == 'List':
        s = AbiListSerializer(eos_type)
        return s.deserialize(binary)
    elif issubclass(eos_type, eos_types.BaseAbiObject):
        # if this is a basic ABI object, serialize it
        return deserialize(binary, eos_type)

    # if type is not supported, raise an Exception
    raise EosSerializerUnsupportedTypeException(eos_type)


def encode(obj, field_name):
    field = obj.__dataclass_fields__[field_name]
    value = getattr(obj, field_name)
    return encode_eos_type(field.type, value)


def decode(abi_class, field_name, binary):
    field = abi_class.__dataclass_fields__[field_name]
    return decode_eos_type(field.type, binary)


def serialize(obj):
    assert issubclass(obj.__class__, eos_types.BaseAbiObject)
    return b''.join(
        encode(obj, field) for field in obj._serializable_fields()
    )


def deserialize(binary, abi_class):
    cursor = 0
    values = {}
    for field in abi_class._serializable_fields():
        length, values[field] = decode(abi_class, field, binary[cursor:])
        cursor += length
    return cursor, abi_class(**values)
