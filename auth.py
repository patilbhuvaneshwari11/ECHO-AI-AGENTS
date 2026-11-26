import hashlib
import os
import hmac
import time
from collections import defaultdict, deque

from audit import log


# Password hashing

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


# Account lockout

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


# Authentication and audit logging

def authenticate(username, password, user_record):
    """Authenticate a user and record the login event."""

    role = user_record.get("role", "unknown") if user_record else "unknown"

    if is_locked_out(username):
        log(
            "login_blocked",
            role,
            {"username": username, "reason": "account_locked"}
        )
        return False, "Account temporarily locked."

    stored_hash = user_record.get("password_hash") if user_record else None

    try:
        valid = (
            isinstance(password, str)
            and isinstance(stored_hash, str)
            and bool(stored_hash)
            and verify_password(password, stored_hash)
        )
    except (ValueError, TypeError, AttributeError):
        valid = False

    if not valid:
        locked = record_failed_login(username)

        log(
            "login_failed",
            role,
            {"username": username, "reason": "invalid_credentials"}
        )

        if locked:
            log(
                "account_locked",
                role,
                {"username": username, "duration_seconds": LOCKOUT_TIME}
            )

        return False, "Invalid username or password."

    reset_login_attempts(username)

    log(
        "login_success",
        role,
        {"username": username}
    )

    return True, "Login successful."