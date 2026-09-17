import sys
from cryptography.fernet import Fernet

pepper = sys.argv[1]
key    = None

with open(sys.argv[2], "rb") as key_file:
    key = key_file.read()

fernet    = Fernet(key)
encPepper = fernet.encrypt(pepper.encode())

with open(sys.argv[3], "wb") as pepper_file:
    pepper_file.write(encPepper)
