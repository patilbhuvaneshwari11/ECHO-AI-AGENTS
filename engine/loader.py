from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"


def to_min(t):
	"""'09:30' -> 570 (minutes since midnight)."""
	h, m = t.split(":")
	return int(h) * 60 + int(m)


def load_data():
	rooms = pd.read_csv(DATA / "rooms.csv")
	exams = pd.read_csv(DATA / "exams.csv")
	enroll = pd.read_csv(DATA / "enrollments.csv")
	dist = pd.read_csv(DATA / "distances.csv")
	validate_rooms(rooms)
	return rooms, exams, enroll, dist


def validate_rooms(rooms):
	"""Reject tampered data such as capacity 0 or 99999."""
	bad = rooms[(rooms.capacity < 1) | (rooms.capacity > 1000)]
	if len(bad) > 0:
		raise ValueError(f"Invalid room capacity in: {list(bad.room_id)}")


def add_minutes(exams):
	exams = exams.copy()
	exams["start_min"] = exams["start"].map(to_min)
	exams["end_min"] = exams["end"].map(to_min)
	return exams
