import unittest
from security import can_modify_slot


class TestStaffAccess(unittest.TestCase):

    def test_staff_can_modify_own_slot(self):
        self.assertTrue(
            can_modify_slot("staff1", "staff1")
        )

    def test_staff_cannot_modify_other_slot(self):
        self.assertFalse(
            can_modify_slot("staff1", "staff2")
        )

    def test_missing_staff_id_denied(self):
        self.assertFalse(
            can_modify_slot("", "staff1")
        )


if __name__ == "__main__":
    unittest.main()