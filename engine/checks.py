from .loader import add_minutes


def _overlap(a, b):
	"""True if two exam records are on the same day and their times overlap."""
	return (
		a["date"] == b["date"]
		and a["start_min"] < b["end_min"]
		and b["start_min"] < a["end_min"]
	)


def _walk(dist, b1, b2):
	"""Walking minutes between two blocks (0 if same block, 15 if unknown)."""
	if b1 == b2:
		return 0
	row = dist[
		((dist.from_block == b1) & (dist.to_block == b2))
		| ((dist.from_block == b2) & (dist.to_block == b1))
	]
	return int(row.iloc[0]["walking_minutes"]) if len(row) else 15


def find_clashes(exams, enroll):
	"""Students who have two exams at the same time."""
	merged = enroll.merge(add_minutes(exams), on="exam_id")
	found = []
	for student, grp in merged.groupby("student_id"):
		rows = grp.to_dict("records")
		for i in range(len(rows)):
			for j in range(i + 1, len(rows)):
				if _overlap(rows[i], rows[j]):
					found.append(
						{"student": student, "exams": [rows[i]["exam_id"], rows[j]["exam_id"]]}
					)
	return found


def find_overloads(exams, rooms):
	"""Exams with more students than the room can hold."""
	merged = exams.merge(rooms[["room_id", "capacity"]], on="room_id")
	bad = merged[merged.expected_students > merged.capacity]
	return [
		{
			"exam": r.exam_id,
			"room": r.room_id,
			"students": int(r.expected_students),
			"capacity": int(r.capacity),
			"over_pct": round(100 * (r.expected_students - r.capacity) / r.capacity),
		}
		for r in bad.itertuples()
	]


def find_double_bookings(exams):
	"""Two exams in the same room at overlapping times."""
	rows = add_minutes(exams).to_dict("records")
	found = []
	for i in range(len(rows)):
		for j in range(i + 1, len(rows)):
			if rows[i]["room_id"] == rows[j]["room_id"] and _overlap(rows[i], rows[j]):
				found.append(
					{"room": rows[i]["room_id"], "exams": [rows[i]["exam_id"], rows[j]["exam_id"]]}
				)
	return found


def find_travel_problems(exams, enroll, rooms, dist):
	"""Students whose gap between two exams is shorter than the walk between blocks."""
	ex = add_minutes(exams).merge(rooms[["room_id", "block"]], on="room_id")
	merged = enroll.merge(ex, on="exam_id")
	found = []
	for student, grp in merged.groupby("student_id"):
		for _, day in grp.groupby("date"):
			rows = day.sort_values("start_min").to_dict("records")
			for a, b in zip(rows, rows[1:]):
				gap = b["start_min"] - a["end_min"]
				if gap < 0:
					continue  # overlapping exams are reported as a clash instead
				need = _walk(dist, a["block"], b["block"])
				if gap < need:
					found.append(
						{
							"student": student,
							"from_exam": a["exam_id"],
							"to_exam": b["exam_id"],
							"gap_min": gap,
							"walk_min": need,
						}
					)
	return found

