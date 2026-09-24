# This is the "service layer": where the real business logic lives,
# kept separate from routes/readiness.py (which only deals with HTTP).
# Routes should stay thin; services do the actual work. This makes the
# logic easy to unit-test without needing to spin up a Flask request.
def calculate_readiness(answers: dict) -> dict:
    """Turn a set of readiness answers into a readiness score between 0-100 %.
        Args:
            answers (dict): A dictionary containing the user's readiness answers.

        Returns:
            dict: A dictionary containing the calculated readiness score.

    """
    # Step 1: are all required answers there?
    if "hasHrvData" not in answers or "gender" not in answers:
        return {"readiness": None, "error": "missing hasHrvData or gender"}

    # Step 2: are the values valid?
    if "monthlyHrv" in answers:
        # float() raises ValueError for text like "abc" or "" and TypeError
        # for None. Catch both so bad input gives a clear error, not a crash.
        try:
            monthly_hrv = float(answers["monthlyHrv"])
        except (ValueError, TypeError):
            return {"readiness": None, "error": "Given HRV is not a number"}
        if monthly_hrv < 0 or monthly_hrv > 500:
            return {"readiness": None, "error": "Given HRV out of range"}
    if "currentHrv" in answers:
        try:
            current_hrv = float(answers["currentHrv"])
        except (ValueError, TypeError):
            return {"readiness": None, "error": "Given HRV is not a number"}
        if current_hrv < 0 or current_hrv > 500:
            return {"readiness": None, "error": "Given HRV out of range"}

    if answers["hasHrvData"] == "No" and answers["gender"] == "Male/No Menstrual Cycle":
        # Type 1, only basis data
        print("Class 1")
    elif answers["hasHrvData"] == "Yes" and answers["gender"] == "Male/No Menstrual Cycle":
        # Type 2, has HRV data, no menstrual cycle
        print("Class 2")
    elif answers["hasHrvData"] == "Yes" and answers["gender"] == "Known Menstrual Cycle":
        # Type 3, has HRV data,  menstrual cycle
        print("Class 3")
    else:
        # Type 4, no HRV data, known menstrual cycle
        print("Class 4")
    return {"readiness": 100}

