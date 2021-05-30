#encode = 'utf-8'
import pytest
import base64
import os

from client import encrypt_intvalue, decrypt_intvalue

print("----- TESTES UNITARIOS -----")
def test_Encrypt():
	cipherkey = os.urandom(16)
	cipherkey_toSend = str(base64.b64encode(cipherkey), 'utf8')
	assert decrypt_intvalue(cipherkey_toSend, encrypt_intvalue(cipherkey_toSend, 1212)) == 1212
	print("*- encrypt, decrypt: PASSOU")

test_Encrypt()