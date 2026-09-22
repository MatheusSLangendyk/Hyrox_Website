from flask import Flask
from flask_cors import CORS

from routes import register_routes

app = Flask(__name__)

# The frontend runs on a different origin (Live Server, e.g. port 5500)
# than this API (port 5000). Browsers block cross-origin requests by
# default, so CORS(app) tells the browser this API allows them.
CORS(app)

register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
