
# TODO: werkzeug version compatibility fix.
#  Need to resolve werkzeug version
#  I tried setting the version to 2.0.3 in setup.py, which has
#  the matching import, but then the installation fails on the build of matplotlib.
#  For now, I'm doing his ad-hoc patch.
try:
    from flask import Flask, request
except ImportError:
    from urllib.parse import quote as url_quote
    from werkzeug import urls
    urls.url_quote = url_quote
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
