import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

password1 = '$Paxful90210'
password2 = '$password1234'

print(f"Hash for {password1}: {hash_password(password1)}")
print(f"Hash for {password2}: {hash_password(password2)}")
