#!/usr/bin/env python3
"""
Password hashing utility script
Usage: python hash_password.py [password]
If no password provided, it will hash "1234567890Qq."
"""
import sys
from src.auth import get_password_hash

def main():
    # Get password from command line or use default
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = "1234567890Qq."
    
    # Generate hash
    hashed = get_password_hash(password)
    
    print(f"Password: {password}")
    print(f"Argon2 Hash: {hashed}")
    print()
    print("For database insertion:")
    print(f"hashed_password = '{hashed}'")
    
    return hashed

if __name__ == "__main__":
    main()