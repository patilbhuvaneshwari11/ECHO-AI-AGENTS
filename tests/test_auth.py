import unittest
from unittest.mock import patch

from auth import (
    hash_password,
    verify_password,
    record_failed_login,
    is_locked_out,
    reset_login_attempts,
    authenticate
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

    @patch("auth.log")
    def test_authenticate_success(self, mock_log):
        password = "CorrectPassword123"

        user_record = {
            "role": "student",
            "password_hash": hash_password(password)
        }

        reset_login_attempts("login_user1")

        result, message = authenticate(
            "login_user1", password, user_record
        )

        self.assertTrue(result)

        mock_log.assert_called_with(
            "login_success",
            "student",
            {"username": "login_user1"}
        )

    @patch("auth.log")
    def test_authenticate_failure(self, mock_log):
        user_record = {
            "role": "student",
            "password_hash": hash_password("CorrectPassword123")
        }

        reset_login_attempts("login_user2")

        result, message = authenticate(
            "login_user2", "WrongPassword123", user_record
        )

        self.assertFalse(result)

        mock_log.assert_called_with(
            "login_failed",
            "student",
            {
                "username": "login_user2",
                "reason": "invalid_credentials"
            }
        )

    @patch("auth.log")
    def test_locked_account_login_blocked(self, mock_log):
        username = "login_user3"
        reset_login_attempts(username)

        for _ in range(5):
            record_failed_login(username)

        result, message = authenticate(
            username, "AnyPassword", None
        )

        self.assertFalse(result)

        mock_log.assert_called_with(
            "login_blocked",
            "unknown",
            {"username": username, "reason": "account_locked"}
        )


if __name__ == "__main__":
    unittest.main()