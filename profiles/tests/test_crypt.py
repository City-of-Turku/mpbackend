from profiles.utils import decrypt_text, encrypt_text


def test_encrypt_and_decrypt():
    in_text = "Hello World"
    key = "1234567890123456"
    ret_vals = encrypt_text(in_text, key)
    dec_text = decrypt_text(ret_vals[0], key, ret_vals[1])
    assert dec_text == in_text
