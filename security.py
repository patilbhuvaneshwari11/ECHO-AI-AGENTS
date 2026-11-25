import re
import time
import csv
from pathlib import Path
from collections import defaultdict, deque
MAX_LEN = 300

BLOCKED_PATTERNS = [
    r"ignore (all |the )?(previous|above|prior) (instructions|rules)",
    r"system prompt",
    r"you are now",
    r"reveal .*(key|prompt|instructions|password)",
    r"<\s*script",
    r"api[_ ]?key",
]


def check_input(text):
    """Returns (True, 'ok') if the text is safe to process, else (False, reason)."""
    text = (text or "").strip()
    if len(text) < 5:
        return False, "Decision is too short."
    if len(text) > MAX_LEN:
        return False, f"Decision is too long (max {MAX_LEN} characters)."
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Blocked: the text looks like an attempt to instruct the AI."
    return True, "ok"


# Role-based access control

ROLE_PERMISSIONS = {
    "admin": [
        "view_timetable",
        "approve_request",
        "run_simulation",
        "view_audit",
        "manage_users"
    ],
    "staff": [
        "view_timetable",
        "submit_request"
    ],
    "student": [
        "view_timetable",
        "submit_feedback"
    ]
}


def has_permission(role, action):
    """Check whether a role is allowed to perform an action."""
    return action in ROLE_PERMISSIONS.get(role, [])


def can_run(role):
    """Check whether a user can run simulations."""
    return has_permission(role, "run_simulation")

# Student feedback rate limiting

MAX_FEEDBACK = 5
FEEDBACK_WINDOW = 3600

feedback_submissions = defaultdict(deque)


def validate_feedback(student_id, feedback):
    """Validate feedback and limit each student to 5 submissions per hour."""

    allowed, reason = check_input(feedback)

    if not allowed:
        return False, reason

    valid_reference, reference_reason = validate_lab_reference(feedback)

    if not valid_reference:
        return False, reference_reason

    now = time.monotonic()
    submissions = feedback_submissions[student_id]

    while submissions and now - submissions[0] >= FEEDBACK_WINDOW:
        submissions.popleft()

    if len(submissions) >= MAX_FEEDBACK:
        return False, "Feedback limit reached. Try again later."

    submissions.append(now)

    return True, "Feedback accepted."

# Staff timetable ownership validation

def can_modify_slot(authenticated_staff_id, slot_owner_id):
    """Allow staff to modify only their own timetable slots."""

    if not authenticated_staff_id or not slot_owner_id:
        return False

    return authenticated_staff_id == slot_owner_id

# Room and laboratory reference validation

ROOMS_FILE = Path(__file__).resolve().parent / "data" / "rooms.csv"

LAB_REFERENCE_PATTERN = re.compile(
    r"\b(?:lab(?:oratory)?|room)\b\s*(?:in\s+|[-:#]\s*)?([A-Z]\d{3})\b"
    r"|\b([A-Z]\d{3})\s+(?:lab(?:oratory)?|room)\b",
    re.IGNORECASE
)


def validate_lab_reference(feedback):
    """Check whether a referenced room/lab ID exists."""

    matches = LAB_REFERENCE_PATTERN.finditer(feedback or "")

    room_ids = [
        (match.group(1) or match.group(2)).upper()
        for match in matches
    ]

    if not room_ids:
        return True, "No room/lab reference found."

    try:
        with ROOMS_FILE.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames or "room_id" not in reader.fieldnames:
                return False, "Room directory is invalid."

            valid_rooms = {
                row["room_id"].strip().upper()
                for row in reader
                if row.get("room_id")
            }

    except (OSError, csv.Error, UnicodeError):
        return False, "Unable to verify room information."

    for room_id in room_ids:
        if room_id not in valid_rooms:
            return False, f"Unknown room/lab ID: {room_id}."

    return True, "Room/lab reference valid."