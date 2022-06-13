from flask import Flask, request
from flask_cors import CORS


def run_flask_app(port, answer_queue):
    app = Flask(__name__)
    CORS(app)

    @app.route('/ping')
    def pong():
        return 'pong'

    @app.route('/answer', methods=['POST'])
    def dialog_answer():
        answer_queue.put(request.json["option"])
        return 'done'

    app.run('0.0.0.0', port=port)
