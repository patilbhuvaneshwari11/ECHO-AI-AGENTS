from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)


def srange(a, b):
	"""S001..S300 style student ids from number a to number b (inclusive)."""
	return [f"S{n:03d}" for n in range(a, b + 1)]


rooms = pd.DataFrame(
	[
		["A101", "A", 0, 60, True],
		["A201", "A", 2, 80, False],
		["B101", "B", 0, 120, True],
		["B102", "B", 0, 90, True],
		["C101", "C", 0, 100, True],
		["C201", "C", 1, 50, False],
	],
	columns=["room_id", "block", "floor", "capacity", "has_lift"],
)

distances = pd.DataFrame(
	[["A", "B", 5], ["B", "C", 8], ["A", "C", 12]],
	columns=["from_block", "to_block", "walking_minutes"],
)

# Who sits which exam. Planted on purpose (see the plan):
# - students S001-S004 sit E05 and E06 at the same time -> 4 clashes
# - E08 has 55 students in a 50-seat room -> 1 overload
# - S251-S270 take E01 then E04, S196-S215 take E02 then E03 (only 10 min apart)
students_in = {
	"E01": srange(1, 90) + srange(251, 270),
	"E02": srange(111, 175) + srange(196, 215),
	"E03": srange(196, 250),
	"E04": srange(251, 300),
	"E05": srange(1, 58),
	"E06": srange(1, 4) + srange(101, 161),
	"E07": srange(201, 300),
	"E08": srange(121, 175),
}

schedule = [
	# exam_id, course, date, start, end, room_id
	["E01", "CS101", "2026-12-01", "09:00", "12:00", "B101"],
	["E02", "MA101", "2026-12-01", "09:00", "12:00", "B102"],
	["E03", "PH101", "2026-12-01", "12:10", "15:10", "A101"],
	["E04", "EE101", "2026-12-01", "12:10", "15:10", "A201"],
	["E05", "CH101", "2026-12-02", "09:00", "12:00", "A101"],
	["E06", "BI101", "2026-12-02", "09:00", "12:00", "C101"],
	["E07", "EN101", "2026-12-02", "13:00", "16:00", "B101"],
	["E08", "HI101", "2026-12-02", "13:00", "16:00", "C201"],
]

exams = pd.DataFrame(
	[row + [len(students_in[row[0]])] for row in schedule],
	columns=["exam_id", "course", "date", "start", "end", "room_id", "expected_students"],
)

enrollments = pd.DataFrame(
	[(s, exam) for exam, studs in students_in.items() for s in studs],
	columns=["student_id", "exam_id"],
)

rooms.to_csv(OUT / "rooms.csv", index=False)
exams.to_csv(OUT / "exams.csv", index=False)
enrollments.to_csv(OUT / "enrollments.csv", index=False)
distances.to_csv(OUT / "distances.csv", index=False)

print("Done. Files written to", OUT)
print(exams)
