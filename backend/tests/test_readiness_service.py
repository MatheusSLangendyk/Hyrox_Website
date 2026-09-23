import pytest
from services.readiness import calculate_readiness


def test_returns_dict_with_readiness_key():
    result = calculate_readiness({})
    assert isinstance(result, dict)
    assert "readiness" in result


def test_placeholder_always_returns_100():
    # Current implementation is a placeholder; update this test when
    # real scoring lands.
    assert calculate_readiness({})["readiness"] == 100
    assert calculate_readiness({"fatigue": "Exhausted"})["readiness"] == 100


@pytest.mark.parametrize(
    "answers",
    [
        {},
        {"fatigue": "Normal"},
        {
            "fatigue": "Normal",
            "sleepHours": "7-8 hours",
            "sleepQuality": "Normal",
            "soreness": "Normal",
            "mentalState": "Normal",
            "hasHrvData": "No",
            "gender": "Male/No Menstrual Cycle",
        },
    ],
)
def test_accepts_various_answer_shapes(answers):
    result = calculate_readiness(answers)
    assert 0 <= result["readiness"] <= 100


def test_does_not_mutate_input():
    answers = {"fatigue": "Normal"}
    snapshot = dict(answers)
    calculate_readiness(answers)
    assert answers == snapshot
