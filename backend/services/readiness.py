# This is the "service layer": where the real business logic lives,
# kept separate from routes/readiness.py (which only deals with HTTP).
# Routes should stay thin; services do the actual work. This makes the
# logic easy to unit-test without needing to spin up a Flask request.
def calculate_readiness(answers: dict) -> dict:
    """Turn a set of readiness answers into a readiness score.

    This is a placeholder: it always returns 100%. The real scoring
    logic (per-answer points and weighting) will replace this body.
    """
    return {"readiness": 100}

