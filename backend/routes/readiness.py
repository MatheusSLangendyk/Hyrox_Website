
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

    # The service decides *whether* the input is invalid; the route decides
    # what that means in HTTP. 400 = "Bad Request" (the client sent bad data).
    if "error" in result:
        return jsonify(result), 400

    # jsonify() converts the Python dict back into a JSON HTTP response
    # (status 200 = "OK" by default)
    return jsonify(result)
