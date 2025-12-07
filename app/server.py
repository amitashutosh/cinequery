from flask import Flask, request, jsonify
from flask_cors import cross_origin
from llm_interface import CineQueryEngine

app = Flask(__name__)

try:
    QUERY_ENGINE = CineQueryEngine()
    print("CineQuery Engine successfully loaded.")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize CineQueryEngine. Database might be missing. Error: {e}")
    QUERY_ENGINE = None

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Welcome to CineQuery API. Use the /query endpoint to submit natural language movie queries."
    })

"""
Accepts a user query (natural language) and returns the synthesized answer.
"""
@app.route('/query', methods=['GET', 'POST'])
@cross_origin(origins='*')
def handle_query():
    if not QUERY_ENGINE:
        return jsonify({"status": "error", "message": "API service is unavailable. Database failed to load."}), 503

    try:
        if request.method == 'POST':
            data = request.get_json()
            user_query = data.get('query')
        elif request.method == 'GET':
            user_query = request.args.get('query')

        if not user_query:
            return jsonify({"status": "error", "message": "Missing 'query' parameter in request body."}), 400

        print(f"Received query: {user_query}")

        result = QUERY_ENGINE.run_cinequery(user_query)

        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except ValueError as e:
        return jsonify({"status": "error", "message": f"Configuration Error: {e}"}), 500
    except Exception as e:
        print(f"Unexpected error during query processing: {e}")
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500


if __name__ == '__main__':
    # Running locally
    app.run(host='0.0.0.0', port=5001, debug=True)
