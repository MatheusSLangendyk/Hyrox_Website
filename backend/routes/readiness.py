
from flask import Blueprint, jsonify, request
from services.readiness import calculate_readiness

readiness_bp = Blueprint("readiness", __name__)


# Registers this function to run whenever a POST request hits /api/readiness
@readiness_bp.route("/api/readiness", methods=["POST"])
def readiness():
    # request.get_json() parses the JSON body the frontend sent
    # (the answers object built by collectAnswers() in main.js)
    answers = request.get_json()
    result = calculate_readiness(answers)

    # jsonify() converts the Python dict back into a JSON HTTP response
    return jsonify(result)
