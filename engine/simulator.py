from .loader import load_data
from .checks import find_clashes, find_overloads, find_double_bookings, find_travel_problems
from .scorer import risk_score


def run_checks(exams, rooms, enroll, dist):
	return {
		"clash": find_clashes(exams, enroll),
		"overload": find_overloads(exams, rooms),
		"double_booking": find_double_bookings(exams),
		"travel": find_travel_problems(exams, enroll, rooms, dist),
	}


def pick_targets(exams, rooms, decision):
	"""Which exams does the decision move?"""
	with_block = exams.merge(rooms[["room_id", "block"]], on="room_id", how="left")
	ids = set(decision.get("exam_ids") or [])
	src = decision.get("source_block")
	if src == "ALL":
		ids |= set(with_block.exam_id)
	elif src:
		ids |= set(with_block[with_block.block == src].exam_id)
	return [e for e in exams.exam_id if e in ids]


def move_all_to_biggest_room(exams, rooms, targets, dest):
	"""Do exactly what was proposed: every target exam goes to the biggest room of the block."""
	new = exams.copy()
	dest_rooms = rooms[rooms.block == dest].sort_values("capacity", ascending=False)
	if len(dest_rooms) > 0:
		new.loc[new.exam_id.isin(targets), "room_id"] = dest_rooms.iloc[0].room_id
	return new


def move_safely(exams, rooms, enroll, dist, targets, dest):
	"""Try each move one by one. Keep it only if the risk score does not get worse."""
	current = exams.copy()
	current_score = risk_score(run_checks(current, rooms, enroll, dist))["score"]
	dest_rooms = rooms[rooms.block == dest].sort_values("capacity")  # smallest first
	for exam_id in targets:
		best = None
		for room in dest_rooms.itertuples():
			trial = current.copy()
			trial.loc[trial.exam_id == exam_id, "room_id"] = room.room_id
			score = risk_score(run_checks(trial, rooms, enroll, dist))["score"]
			if score <= current_score and (best is None or score < best[0]):
				best = (score, room.room_id)
		if best:
			current.loc[current.exam_id == exam_id, "room_id"] = best[1]
			current_score = best[0]
	return current


def moved_exams(before, after):
	b = before.set_index("exam_id")["room_id"]
	a = after.set_index("exam_id")["room_id"]
	return [e for e in b.index if a[e] != b[e]]


def findings(results):
	"""Turn raw check results into plain sentences. All of these are 'computed'."""
	out = []
	students = {c["student"] for c in results["clash"]}
	if students:
		out.append({"source": "computed", "severity": "high",
					"text": f"{len(students)} student(s) have two exams at the same time."})
	for o in results["overload"]:
		out.append({"source": "computed", "severity": "high",
					"text": f"Exam {o['exam']} has {o['students']} students but room {o['room']} "
							f"holds {o['capacity']} ({o['over_pct']}% over)."})
	for d in results["double_booking"]:
		out.append({"source": "computed", "severity": "critical",
					"text": f"Room {d['room']} is booked for {d['exams'][0]} and "
							f"{d['exams'][1]} at the same time."})
	walkers = {t["student"] for t in results["travel"]}
	if walkers:
		out.append({"source": "computed", "severity": "medium",
					"text": f"{len(walkers)} student(s) cannot walk to their next exam "
							f"in the time between exams."})
	return out


def simulate(decision):
	"""The one function the screen calls. Returns three options, scored."""
	rooms, exams, enroll, dist = load_data()
	dest = decision["destination_block"]
	targets = pick_targets(exams, rooms, decision)
	variants = [
		("Keep the current plan", "Change nothing.", exams),
		("Do exactly what was proposed",
		 "Move every selected exam to the biggest room of the block.",
		 move_all_to_biggest_room(exams, rooms, targets, dest)),
		("Safer version",
		 "Move an exam only if that does not raise the risk score.",
		 move_safely(exams, rooms, enroll, dist, targets, dest)),
	]
	options = []
	for name, desc, ex in variants:
		results = run_checks(ex, rooms, enroll, dist)
		options.append({
			"name": name, "description": desc,
			"moved": moved_exams(exams, ex),
			"results": results,
			"risk": risk_score(results),
			"findings": findings(results),
		})
	# lowest risk wins; on a tie, prefer the option that carries out more of the decision
	best = min(range(len(options)),
			   key=lambda i: (options[i]["risk"]["score"], -len(options[i]["moved"])))
	return {"options": options, "recommended": best, "targets": targets}
