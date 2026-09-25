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

# ratio = current_hrv / monthly_hrv
HRV_LOOK_UP_TABLE = [
    (0, 25),
    (0.2, 25),
    (0.50, 50),   # ratio < 0.50
    (0.80, 70),   # ratio < 0.80
    (0.90, 100),   # 0.80 <= ratio < 0.90
    (1.00, 100),   # 0.90 <= ratio < 1.00
    (float("inf"), 100),  # ratio >= 1.10  (inf = "everything above")
]

# cycle phase -> readiness
# The phases must match the <option value="..."> strings in index.html.
MENSTRUAL_LOOK_UP_TABLE = {
    "Menstrual":  75,
    "Follicular": 100,
    "Ovulation":  100,
    "Luteal":     80,
}

BASELINE_GRADE = 4.0 #Grade by which the readiness is still 100 %


def interpolate_hrv_readiness(ratio: float) -> float:
    """Look up the readiness for an HRV ratio in HRV_LOOK_UP_TABLE.

    Between two table points the readiness is linearly interpolated,
    e.g. with (0.5, 50) and (0.8, 70) a ratio of 0.65 gives 60.
    """
    for i in range(len(HRV_LOOK_UP_TABLE) - 1):
        lower_ratio, lower_readiness = HRV_LOOK_UP_TABLE[i]
        upper_ratio, upper_readiness = HRV_LOOK_UP_TABLE[i + 1]

        if lower_ratio <= ratio < upper_ratio:
            # The last point is infinity: nothing to interpolate towards,
            # so everything above the last real point keeps its readiness.
            if upper_ratio == float("inf"):
                return lower_readiness

            # How far the ratio lies between the two points (0.0 to 1.0)
            fraction = (ratio - lower_ratio) / (upper_ratio - lower_ratio)
            return lower_readiness + fraction * (upper_readiness - lower_readiness)

    # Ratio below the first table point: use the first readiness
    return HRV_LOOK_UP_TABLE[0][1]


def calculate_readiness(answers: dict) -> dict:
    """Turn a set of readiness answers into a readiness score between 0-100 %.
        Args:
            answers (dict): A dictionary containing the user's readiness answers.

        Returns:
            dict: A dictionary containing the calculated readiness score.

    """
    #Step 0 Initialize Data
    monthly_hrv = None
    current_hrv = None
    hrv_readiness = None
    menstrual_readiness = None

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
    #Calculate HRV based readiness
    
    if monthly_hrv is not None and current_hrv is not None:
        hrv_readiness = interpolate_hrv_readiness(current_hrv / monthly_hrv)
    if "cyclePhase" in answers:
        cycle_phase = answers["cyclePhase"]
        menstrual_readiness = float(MENSTRUAL_LOOK_UP_TABLE[cycle_phase])
   
   
    if answers["hasHrvData"] == "No" and answers["gender"] == "Male/No Menstrual Cycle":
        # Type 1, only basis data
        readiness = baseline_readiness
    elif answers["hasHrvData"] == "Yes" and answers["gender"] == "Male/No Menstrual Cycle":
        # Type 2, has HRV data, no menstrual cycle
        if hrv_readiness is None:
            # "Yes" was selected but no HRV values were sent
            readiness = baseline_readiness
        else:
            readiness = 0.5*baseline_readiness + 0.5*hrv_readiness
    elif answers["hasHrvData"] == "Yes" and answers["gender"] == "Known Menstrual Cycle":
        # Type 3, has HRV data,  menstrual cycle
        readiness = (baseline_readiness + menstrual_readiness + hrv_readiness) / 3
    else:
        # Type 4, no HRV data, known menstrual cycle
        readiness = baseline_readiness*0.5 + menstrual_readiness*0.5
    return {"readiness": int(readiness)}
