from datetime import datetime, timezone

import pytest

from aioeos import serializer, types, exceptions


def test_unsupported_type_exception():
    with pytest.raises(exceptions.EosSerializerUnsupportedTypeException):
        serializer.get_abi_type_serializer(None)


def test_abi_name_serializer():
    s = serializer.AbiNameSerializer()
    name = 'eosio.token'
    serialized = s.serialize(name)
    assert serialized == b'\x00\xa6\x824\x03\xea0U'

    # serializing and deserializing should produce the same value
    _, deserialized = s.deserialize(serialized)
    assert deserialized == name


def test_abi_name_serializer_13th_char():
    s = serializer.AbiNameSerializer()
    name = 'eosio.testing'
    serialized = s.serialize(name)
    assert serialized == b'<]\xc6*\x03\xea0U'

    # serializing and deserializing should produce the same value
    _, deserialized = s.deserialize(serialized)
    assert deserialized == name


def test_abi_name_serializer_validation():
    s = serializer.AbiNameSerializer()

    with pytest.raises(exceptions.EosSerializerAbiNameTooLongException):
        s.serialize('dfisdjfiosdjfiosdjfiodsfjo')

    with pytest.raises(
        exceptions.EosSerializerAbiNameInvalidCharactersException
    ):
        s.serialize('eosio;9852')


def test_basic_type_serializer():
    examples = {
        types.UInt8: 5,
        types.UInt16: 30,
        types.UInt64: 2394823409,
        types.Int8: -5,
        types.Int16: -30,
        types.Int64: -2394823409
    }
    encoded = {
        abi_type: (
            serializer.get_abi_type_serializer(abi_type).serialize(value)
        )
        for abi_type, value in examples.items()
    }
    decoded = {
        abi_type: (
            serializer.get_abi_type_serializer(abi_type).deserialize(value)[1]
        )
        for abi_type, value in encoded.items()
    }

    # let's make an assumption, that if example values are not the same as
    # their encoded representation, we did the thing
    assert examples != encoded
    assert examples == decoded


def test_string_serializer():
    s = serializer.AbiStringSerializer()
    value = 'Really random string for testing'
    encoded = s.serialize(value)
    _, decoded = s.deserialize(encoded)
    assert value == decoded
    assert encoded != decoded


def test_abi_bytes_serializer():
    s = serializer.AbiBytesSerializer()
    value = b'\x00\x21\x37\x00'
    encoded = s.serialize(value)
    _, decoded = s.deserialize(encoded)
    assert value == decoded
    assert encoded != decoded


def test_time_point_sec_serializer():
    s = serializer.AbiTimePointSecSerializer()

    # drop anything below seconds
    value = datetime.now(timezone.utc).replace(microsecond=0)

    encoded = s.serialize(value)
    _, decoded = s.deserialize(encoded)
    assert value == decoded
    assert encoded != decoded


def test_time_point_serializer():
    s = serializer.AbiTimePointSerializer()

    # round datetime to miliseconds
    value = datetime.now(timezone.utc)
    value = value.replace(
        microsecond=int(int(value.microsecond / 1000) * 1000)
    )

    encoded = s.serialize(value)
    _, decoded = s.deserialize(encoded)
    assert value == decoded
    assert encoded != decoded


def test_varuint_serializer():
    s = serializer.VarUIntSerializer()
    value = 298409234
    encoded = s.serialize(value)
    _, decoded = s.deserialize(encoded)
    assert value == decoded
    assert encoded != decoded


def test_eos_authorization_serializer():
    value = types.EosPermissionLevel(actor='eosio', permission='active')
    encoded = serializer.serialize(value)
    assert encoded == b'\x00\x00\x00\x00\x00\xea0U\x00\x00\x00\x00\xa8\xed22'
    length, decoded = serializer.deserialize(encoded, types.EosPermissionLevel)
    assert decoded == value
    assert len(encoded) == length


def test_eos_action_serializer():
    authorizations = [
        types.EosPermissionLevel(actor='eosio', permission='active'),
        types.EosPermissionLevel(actor='cryptobakery', permission='active')
    ]
    action = types.EosAction(
        account='eosio',
        name='newaccount',
        authorization=authorizations,
        data=b'\x00\x21\x37\x00'
    )
    encoded = serializer.serialize(action)
    assert encoded == (
        b'\x00\x00\x00\x00\x00\xea0U\x00@\x9e\x9a"d\xb8\x9a\x02\x00\x00\x00'
        b'\x00\x00\xea0U\x00\x00\x00\x00\xa8\xed22\xe0\xaf\x82\xe6\xd0\\\xfd'
        b'E\x00\x00\x00\x00\xa8\xed22\x04\x00!7\x00'
    )
    length, decoded = serializer.deserialize(encoded, types.EosAction)
    assert decoded == action
    assert len(encoded) == length


def test_eos_transaction_deserialize():
    """
    Test deserialization logic on a known valid TX from EOS blockchain.
    """
    bin_tx = (
        b'\xa8\xaa\xca]\x86\xadwB\x7f\xb8\x00\x00\x00\x00\x01\x10T\xd4~\x1a'
        b'\x17\xa7{\x00\x00\x00\x00\xa8l\xd4E\x01\x10T\xd4~\x1a\x17\xa7{\x00'
        b'\x00\x00\x00\xa8\xed22\xac\x02\x10T\xd4~\x1a\x17\xa7{O(\xe9\xaa\x8c'
        b'\xe8\xaf\x81\xe5\xaf\x86\xe9\x92\xa5):6a3167056a9df5a039ef441b6159d'
        b'2bef8e9b7337120c43c8140b9ee1f085adf\x1b(\xe6\xb8\xb8\xe6\x88\x8f\xe5'
        b'\x90\x8d\xe7\xa7\xb0):\xe4\xb8\x80\xe9\xa3\x9e\xe5\x86\xb2\xe5\xa4'
        b'\xa9\x11(\xe6\x88\xbf\xe9\x97\xb4ID):230005"(\xe5\xbc\x80\xe5\xa7'
        b'\x8b\xe6\x97\xb6\xe9\x97\xb4):2019-11-12 20:42:15"(\xe7\xbb\x93\xe6'
        b'\x9d\x9f\xe6\x97\xb6\xe9\x97\xb4):2019-11-12 20:42:29\xe8\xb3\x01'
        b'\x00\x00\x00\x00\x00"(\xe5\xbd\x93\xe5\xb1\x80\xe5\xb1\x80\xe5\x8f'
        b'\xb7):1194233921144421632\x15(\xe5\xbd\x93\xe5\xb1\x80\xe5\xbc\x80'
        b'\xe7\x89\x8c\xe7\xbb\x93\xe6\x9e\x9c):\x16(\xe6\xb8\xb8\xe6\x88\x8f'
        b'\xe7\xbb\x93\xe6\x9e\x9c):2.3 \xe5\x80\x8d\xc8 \xaa_n\x01\x00\x00'
        b'\x00'
    )
    expected = types.EosTransaction(
        expiration=datetime.fromisoformat('2019-11-12T12:50:48.000+00:00'),
        ref_block_num=44422,
        ref_block_prefix=3095347831,
        max_net_usage_words=0,
        max_cpu_usage_ms=0,
        delay_sec=0,
        context_free_actions=[],
        actions=[
            types.EosAction(
                account='jinlianyule1',
                name='create',
                authorization=[
                    types.EosPermissionLevel(
                        actor='jinlianyule1',
                        permission='active'
                    )
                ],
                data=(
                    b'\x10T\xd4~\x1a\x17\xa7{O(\xe9\xaa\x8c\xe8\xaf\x81\xe5'
                    b'\xaf\x86\xe9\x92\xa5):6a3167056a9df5a039ef441b6159d2b'
                    b'ef8e9b7337120c43c8140b9ee1f085adf\x1b(\xe6\xb8\xb8\xe6'
                    b'\x88\x8f\xe5\x90\x8d\xe7\xa7\xb0):\xe4\xb8\x80\xe9\xa3'
                    b'\x9e\xe5\x86\xb2\xe5\xa4\xa9\x11(\xe6\x88\xbf\xe9\x97'
                    b'\xb4ID):230005"(\xe5\xbc\x80\xe5\xa7\x8b\xe6\x97\xb6'
                    b'\xe9\x97\xb4):2019-11-12 20:42:15"(\xe7\xbb\x93\xe6'
                    b'\x9d\x9f\xe6\x97\xb6\xe9\x97\xb4):2019-11-12 20:42:29'
                    b'\xe8\xb3\x01\x00\x00\x00\x00\x00"(\xe5\xbd\x93\xe5\xb1'
                    b'\x80\xe5\xb1\x80\xe5\x8f\xb7):1194233921144421632\x15'
                    b'(\xe5\xbd\x93\xe5\xb1\x80\xe5\xbc\x80\xe7\x89\x8c\xe7'
                    b'\xbb\x93\xe6\x9e\x9c):\x16(\xe6\xb8\xb8\xe6\x88\x8f\xe7'
                    b'\xbb\x93\xe6\x9e\x9c):2.3 \xe5\x80\x8d\xc8 \xaa_n\x01'
                    b'\x00\x00'
                )
            )
        ],
        transaction_extensions=[]
    )
    encoded = serializer.serialize(expected)
    length, decoded = serializer.deserialize(bin_tx, types.EosTransaction)
    assert encoded == bin_tx
    assert decoded == expected
    assert len(bin_tx) == length


def test_eos_transaction_serializer():
    authorizations = [
        types.EosPermissionLevel(actor='eosio', permission='active'),
        types.EosPermissionLevel(actor='cryptobakery', permission='active')
    ]
    action = types.EosAction(
        account='eosio',
        name='newaccount',
        authorization=authorizations,
        data=b'\x00\x21\x37\x00'
    )
    transaction = types.EosTransaction(
        expiration=datetime(
            year=2019,
            month=10,
            day=5,
            hour=3,
            minute=30,
            second=25,
            tzinfo=timezone.utc
        ),
        ref_block_num=3,
        ref_block_prefix=3,
        actions=[action]
    )
    encoded = serializer.serialize(transaction)
    assert encoded == (
        b'Q\x0e\x98]\x03\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00'
        b'\x00\x00\xea0U\x00@\x9e\x9a"d\xb8\x9a\x02\x00\x00\x00\x00\x00\xea0U'
        b'\x00\x00\x00\x00\xa8\xed22\xe0\xaf\x82\xe6\xd0\\\xfdE\x00\x00\x00'
        b'\x00\xa8\xed22\x04\x00!7\x00\x00'
    )
    length, decoded = serializer.deserialize(encoded, types.EosTransaction)
    assert decoded == transaction
    assert len(encoded) == length
