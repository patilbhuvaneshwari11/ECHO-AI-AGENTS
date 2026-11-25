"""Risk scoring for exam scheduling results."""

# Points added for each problem found. Judges can see and change these.
WEIGHTS = {"clash": 2, "overload": 5, "travel": 1, "double_booking": 8}


def risk_score(results, weights=WEIGHTS):
	counts = {
		"clash": len({c["student"] for c in results["clash"]}),
		"overload": len(results["overload"]),
		"travel": len({t["student"] for t in results["travel"]}),
		"double_booking": len(results["double_booking"]),
	}
	breakdown = {key: counts[key] * weights[key] for key in counts}
	return {
		"score": min(100, sum(breakdown.values())),
		"counts": counts,
		"breakdown": breakdown,
	}
