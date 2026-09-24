import pytest
from services.readiness import calculate_readiness


def test_returns_dict_with_readiness_key():
    result = calculate_readiness({})
    assert isinstance(result, dict)
    assert "readiness" in result


def test_lack_input_error():
    # Current implementation is a placeholder; update this test when
    # real scoring lands.
    result =  calculate_readiness({})
    assert result["readiness"] == None
    result = calculate_readiness({"fatigue": "Exhausted"})
    assert result["readiness"] == None

# The minimum answers needed to get past the completeness check,
# so the tests below really reach the HRV validation.
REQUIRED_ANSWERS = {"hasHrvData": "Yes", "gender": "Male/No Menstrual Cycle"}


@pytest.mark.parametrize("out_of_range", ["-1", "501"])
def test_hrv_range(out_of_range):
    result = calculate_readiness({**REQUIRED_ANSWERS, "monthlyHrv": out_of_range})
    assert result["readiness"] == None
    assert result["error"] == "monthlyHrv out of range"

@pytest.mark.parametrize("bad_value", ["abc", "", None])
def test_hrv_not_a_number(bad_value):
    result = calculate_readiness({**REQUIRED_ANSWERS, "currentHrv": bad_value})
    assert result["readiness"] == None
    assert result["error"] == "currentHrv is not a number"

@pytest.mark.parametrize(
    "answers",
    [
        {"fatigue": "Normal",
                    "sleepHours": "7-8 hours",
                    "sleepQuality": "Normal",
                    "soreness": "Normal",
                    "mentalState": "Stressed",
                    "hasHrvData": "No",
                    "monthlyHrv": 100,
                    "currentHrv": 100,
                    "gender": "Male/No Menstrual Cycle",},
        {"fatigue": "Normal",
                    "sleepHours": "7-8 hours",
                    "sleepQuality": "Normal",
                    "soreness": "Normal",
                    "mentalState": "Normal",
                    "hasHrvData": "Yes",
                    "gender": "Male/No Menstrual Cycle",},

        {"fatigue": "Normal",
                    "sleepHours": "7-8 hours",
                    "sleepQuality": "Normal",
                    "soreness": "Normal",
                    "mentalState": "Normal",
                    "hasHrvData": "No",
                    "gender": "Known Menstrual Cycle",
                    "cyclePhase": "Luteal"},

        {"fatigue": "Normal",
                    "sleepHours": "7-8 hours",
                    "sleepQuality": "Normal",
                    "soreness": "Normal",
                    "mentalState": "Normal",
                    "hasHrvData": "Yes",
                    "monthlyHrv": 100,
                    "currentHrv": 100,
                    "gender": "Known Menstrual Cycle",
                    "cyclePhase": "Luteal"}],
)
def test_accepts_various_answer_shapes(answers):
    result = calculate_readiness(answers)
    assert 0 <= result["readiness"] <= 100


def test_does_not_mutate_input():
    answers = {"fatigue": "Normal"}
    snapshot = dict(answers)
    calculate_readiness(answers)
    assert answers == snapshot
