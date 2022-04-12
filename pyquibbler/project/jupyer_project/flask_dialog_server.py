import traceback

from flask import Flask, request
from flask_cors import CORS


def run_flask_app(answer_queue):
    app = Flask(__name__)
    CORS(app)

    @app.route('/ping')
    def pong():
        return 'pong'

    @app.route('/answer', methods=['POST'])
    def dialog_answer():
        open('/tmp/aaa.txt', 'w').write('HELLO!')
        try:
            answer_queue.put(request.json["option"])
        except Exception:
            open('/tmp/aaa.txt', 'w').write(traceback.format_exc())
            raise
        return 'pasten'

    app.run('0.0.0.0', port=8200)