from aioeos import EosKey


def test_eos_key_creating():
    """Checks if we can generate a key and sign something with it"""
    # Both keys should be different
    key1 = EosKey()
    key2 = EosKey()

    # sign an example string with key 1
    example_string = 'Lorem ipsum dolor sit amet amet.'.encode('utf-8')
    signature = key1.sign(example_string)

    # if this is properly signed, only verifying with key 1 should return True
    assert key1.verify(signature, example_string)
    assert not key2.verify(signature, example_string)

    # We should be able to convert the key to wif format and load it
    key3 = EosKey(private_key=key1.to_wif())
    assert key3.verify(signature, example_string)


def test_eos_key_restore():
    # known good WIF key pair
    wif_private = '5KJbQhJSyayfUvfpK1d7sPYBRdjGz1EHgeCE8mfrZC1pM4Z9Tto'
    wif_public = 'EOS72kwLAoSdeVjUgKTCJ9cysF2iQVJehmGMjWrJUfbGnxATgYVRf'

    # known good PVT key pair
    pvt_private = 'PVT_K1_2jH3nnhxhR3zPUcsKaWWZC9ZmZAnKm3GAnFD1xynGJE1Znuvjd'
    pvt_public = 'EOS859gxfnXyUriMgUeThh1fWv3oqcpLFyHa3TfFYC4PK2HqhToVM'

    # should return the same values as the original ones
    wif_key = EosKey(private_key=wif_private)
    assert wif_key.to_public() == wif_public
    assert wif_key.to_wif() == wif_private

    pvt_key = EosKey(private_key=pvt_private)
    assert pvt_key.to_public() == pvt_public
    assert pvt_key.to_pvt() == pvt_private
