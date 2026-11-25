import csv
import sys
from pathlib import Path
from getpass import getpass

# Locate the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from auth import hash_password

USERS_FILE = PROJECT_ROOT / "data" / "users.csv"

ROLES = ["admin", "staff", "student"]


def create_users():

    # Avoid accidentally overwriting existing accounts
    if USERS_FILE.exists():
        print("users.csv already exists. No changes made.")
        return

    users = []
    usernames = set()

    for role in ROLES:
        print(f"\nCreate {role.upper()} account")

        while True:
            username = input("Enter username: ").strip()

            if not username:
                print("Username cannot be empty.")
            elif username in usernames:
                print("Username already used. Choose another.")
            else:
                break

        while True:
            password = getpass("Enter password (minimum 8 characters): ")

            if len(password) < 8:
                print("Password must contain at least 8 characters.")
                continue

            confirm_password = getpass("Confirm password: ")

            if password != confirm_password:
                print("Passwords do not match. Try again.")
            else:
                break

        users.append({
            "username": username,
            "role": role,
            "password_hash": hash_password(password)
        })

        usernames.add(username)

    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with USERS_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["username", "role", "password_hash"]
        )

        writer.writeheader()
        writer.writerows(users)

    print("\nThree user accounts created successfully!")
    print(f"Saved to: {USERS_FILE}")


if __name__ == "__main__":
    create_users()