# This is the "service layer": where the real business logic lives,
# kept separate from routes/readiness.py (which only deals with HTTP).
# Routes should stay thin; services do the actual work. This makes the
# logic easy to unit-test without needing to spin up a Flask request.


# Look-up table for the basic questions.
# Each row is one answer level: the first row holds the best answer of every
# question, the last row the worst one. The last column is the readiness
# score for that row (all 100 for now).
# The answers must match the <option value="..."> strings in index.html.
LOOK_UP_TABLE = [
    # fatigue               sleepHours       sleepQuality          soreness                mentalState                   score
    ["No Fatigue",          "Over 10 hours", "Outstanding",        "No soreness",          "Feeling great-very relaxed", 1.5],
    ["Minimal fatigue",     "9-10 hours",    "Very Good",          "Very little soreness", "Feeling good-relaxed",       2.0],
    ["Better than normal",  "8-9 hours",     "Better than Normal", "Better than normal",   "Better than normal",         3.0],
    ["Normal",              "7-8 hours",     "Normal",             "Normal",               "Normal",                     4.0],
    ["Worse than Normal",   "5-6 hours",     "Worse than Normal",  "Worse than Normal",    "Worse than Normal",          5.0],
    ["Very fatigued",       "4-5 hours",     "Disrupted",          "Very sore",            "Stressed",                   6.0],
    ["Exhausted",           "less than 4",   "Horrible",           "Extremely sore",       "Very Stressed",              10.0],
]

BASELINE_GRADE = 4.0 #Grade by which the readiness is still 100 %

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

    # Step 2: are the HRV values valid?
    if "monthlyHrv" in answers:
        # float() raises ValueError for text like "abc" or "" and TypeError
        # for None. Catch both so bad input gives a clear error, not a crash.
        try:
            monthly_hrv = float(answers["monthlyHrv"])
        except (ValueError, TypeError):
            return {"readiness": None, "error": "Given HRV is not a number"}
        if monthly_hrv < 1 or monthly_hrv > 500:
            return {"readiness": None, "error": "Given HRV must be between 1 and 500"}
    if "currentHrv" in answers:
        try:
            current_hrv = float(answers["currentHrv"])
        except (ValueError, TypeError):
            return {"readiness": None, "error": "Given HRV is not a number"}
        if current_hrv < 1 or current_hrv > 500:
            return {"readiness": None, "error": "Given HRV must be between 1 and 500"}

    #Step 3: Calculate Baseline readiness
    total_grade = 0.0
    NUMBER_OF_BASELINE_QUESTIONS = len(LOOK_UP_TABLE[0])-1
    answer_values = list(answers.values())
    columns = list(zip(*LOOK_UP_TABLE)) #All Columns

    for i in range(NUMBER_OF_BASELINE_QUESTIONS): 
        index = columns[i].index(answer_values[i])  
        current_grade = LOOK_UP_TABLE[index][-1]
        total_grade += float(current_grade)
    #The higher the value of the total_grade, less ready the athlete will be
    baseline_readiness = 100*min(1.0, BASELINE_GRADE*NUMBER_OF_BASELINE_QUESTIONS/total_grade)
    # Step 4: Calculate readiness based on the available data
    # (use LOOK_UP_TABLE, defined at the top of this file)
    if answers["hasHrvData"] == "No" and answers["gender"] == "Male/No Menstrual Cycle":
        # Type 1, only basis data
        readiness = baseline_readiness
    elif answers["hasHrvData"] == "Yes" and answers["gender"] == "Male/No Menstrual Cycle":
        # Type 2, has HRV data, no menstrual cycle
        readiness = baseline_readiness
    elif answers["hasHrvData"] == "Yes" and answers["gender"] == "Known Menstrual Cycle":
        # Type 3, has HRV data,  menstrual cycle
        readiness = baseline_readiness
    else:
        # Type 4, no HRV data, known menstrual cycle
        readiness = baseline_readiness
    return {"readiness": readiness}
