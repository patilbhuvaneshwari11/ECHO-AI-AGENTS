import unittest
from auth import (
    hash_password,
    verify_password,
    record_failed_login,
    is_locked_out,
    reset_login_attempts
)


class TestAuthentication(unittest.TestCase):

    def test_password_is_hashed(self):
        password = "TestPassword123"
        hashed = hash_password(password)
        self.assertNotEqual(password, hashed)

    def test_correct_password(self):
        password = "TestPassword123"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))

    def test_wrong_password(self):
        hashed = hash_password("TestPassword123")
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_account_locks_after_five_failures(self):
        username = "test_user"
        reset_login_attempts(username)

        for _ in range(5):
            record_failed_login(username)

        self.assertTrue(is_locked_out(username))

    def test_account_not_locked_before_five_failures(self):
        username = "test_user2"
        reset_login_attempts(username)

        for _ in range(4):
            record_failed_login(username)

        self.assertFalse(is_locked_out(username))

    def test_successful_login_resets_attempts(self):
        username = "test_user3"
        reset_login_attempts(username)

        for _ in range(4):
            record_failed_login(username)

        reset_login_attempts(username)

        self.assertFalse(is_locked_out(username))


if __name__ == "__main__":
    unittest.main()