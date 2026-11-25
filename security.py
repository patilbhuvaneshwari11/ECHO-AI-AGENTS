import re

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
        "submit_request",
        "approve_request",
        "run_simulation",
        "view_audit",
        "manage_users"
    ],

    "staff": [
        "view_timetable",
        "submit_request"
    ],

    "viewer": [
        "view_timetable"
    ]
}


def has_permission(role, action):
    """Check whether a role is allowed to perform an action."""
    return action in ROLE_PERMISSIONS.get(role, [])


def can_run(role):
    """Check whether a user can run simulations."""
    return has_permission(role, "run_simulation")