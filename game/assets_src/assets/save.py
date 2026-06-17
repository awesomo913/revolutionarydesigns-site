"""High score persistence using JSON."""

import json
from config import SAVE_FILE

MAX_SCORES: int = 5


def load_high_scores() -> list[dict]:
    """Load high scores from disk. Returns sorted list of {score, level}."""
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        scores = data.get("high_scores", [])
        return sorted(scores, key=lambda s: s.get("score", 0), reverse=True)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []


def save_high_score(score: int, level_reached: int) -> bool:
    """Add score if it qualifies for top 5. Returns True if it made the list."""
    scores = load_high_scores()
    entry = {"score": score, "level": level_reached}
    scores.append(entry)
    scores.sort(key=lambda s: s["score"], reverse=True)
    scores = scores[:MAX_SCORES]

    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"high_scores": scores}, f, indent=2)
    except OSError:
        return False

    return entry in scores


def get_best_score() -> int:
    """Return the highest saved score, or 0."""
    scores = load_high_scores()
    return scores[0]["score"] if scores else 0
