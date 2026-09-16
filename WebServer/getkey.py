import sys
from cryptography.fernet import Fernet

message = "The quick brown fox jumped over the lazy dogs."
key = Fernet.generate_key()

with open(sys.argv[1], "wb") as key_file:
    key_file.write(key)

print("Key: " + str(key))

fernet = Fernet(key)
encMessage = fernet.encrypt(message.encode())

print("Original String:  " + message)
print("Encrypted String: " + str(encMessage))

decMessage = fernet.decrypt(encMessage).decode()

print("\nDecrypted String: " + decMessage)
