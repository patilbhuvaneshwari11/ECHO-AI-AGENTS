import re
import time
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