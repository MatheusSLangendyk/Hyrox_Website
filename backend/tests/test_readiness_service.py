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

def test_hrv_range():
    # Current implementation is a placeholder; update this test when
    # real scoring lands.
    assert calculate_readiness({"monthlyHrv": "-1"})["readiness"] == None
    assert calculate_readiness({"monthlyHrv": "501"})["readiness"] == None

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
