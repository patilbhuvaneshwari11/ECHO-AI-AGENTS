import hashlib
import os
import hmac

def hash_password(password):
    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    salt_hex, hash_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)

    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000
    )

    return hmac.compare_digest(new_hash.hex(), hash_hex)

import time
from collections import defaultdict, deque

MAX_ATTEMPTS = 5
LOCKOUT_TIME = 300

failed_attempts = defaultdict(deque)


def record_failed_login(username):
    now = time.monotonic()
    attempts = failed_attempts[username]

    while attempts and now - attempts[0] >= LOCKOUT_TIME:
        attempts.popleft()

    attempts.append(now)

    return len(attempts) >= MAX_ATTEMPTS


def is_locked_out(username):
    now = time.monotonic()
    attempts = failed_attempts[username]

    while attempts and now - attempts[0] >= LOCKOUT_TIME:
        attempts.popleft()

    return len(attempts) >= MAX_ATTEMPTS


def reset_login_attempts(username):
    failed_attempts.pop(username, None)
