import logging
import os
import json
from http import HTTPStatus

from pathlib import Path

import requests
from flask_cors import CORS
from flask_restx import Api, Resource
from gevent.pywsgi import WSGIServer

import config
from flask import Flask, Blueprint, Response
from flask import make_response, jsonify, send_from_directory, url_for
from flask import render_template_string

# impostazione di Flask
from flask import request

from parse_cli import parse_string
from engine.misc.log import set_log

logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='web/static', static_url_path='/res')
app.root_path = os.path.dirname(os.path.abspath(__file__))

SWAGGER_UI_HTML = "swagger-ui.html"
SWAGGER_JSON = '/swagger.json'
http_methods = ['put', 'get', 'del', 'post', 'head']

CORS(app)
blueprint = Blueprint('api', __name__, url_prefix='/')

# Swagger
api = Api(blueprint,
          title="PyPArSe",
          description="Servizio",
          contact="Roberto Battistoni",
          version=config.VERSION,
          contact_email="roberto.battistoni@senato.it",
          doc=f'/{SWAGGER_UI_HTML}')

# app.root_path = os.path.dirname(os.path.abspath(__file__))
app.register_blueprint(blueprint)
nsv = api.namespace('', description='Parser articolati')


@app.route("/v2/api-docs", methods=['GET'])
def get_doc():
    """
    Serve per la redirect della documentazione swagger
    """
    if request.method == 'GET':
        url = url_for(api.endpoint('specs'), _external=True)
        logger.debug(f"url: {url}")

        resp = requests.get(url, timeout=20)
        # excluded_headers = ['content - encoding', 'content - length', 'transfer - encoding', 'connection']
        excluded_headers = []
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                   name.lower() not in excluded_headers]

        json_dict = json.loads(resp.content)

        # Aggiunge le vendor extensions
        json_dict['info']['x-area'] = 'Testi'
        json_dict['info']['x-tipologia'] = 'Servizio'
        json_dict['info']['x-referente'] = 'Roberto Battistoni'

        # aggiungo il campo host
        try:
            json_dict[
                'host'] = f"{os.environ['EUREKA_INSTANCE_HOSTNAME']}:{os.environ['EUREKA_INSTANCE_NONSECUREPORT']}"
        except KeyError as e:
            logger.error("Problema nella variabile di ambiente EUREKA_INSTANCE_HOSTNAME", exc_info=1)
            pass

        response = Response(json.dumps(json_dict), resp.status_code, headers)
        return response


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'web/static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/ROBOTS.TXT')
def robots():
    return send_from_directory(os.path.join(app.root_path, 'web/static'),
                               'ROBOTS.TXT', mimetype='text/plain')


@app.route('/app', methods=['GET'])
def parse_web_page():
    """
    Ritorna l'interfaccia Web
    :return:
    """
    full_path = os.path.join(app.root_path, 'web/static/html/web.html')
    with open(full_path, "r", encoding="iso-8859-1") as f:
        source = f.read()
        return render_template_string(source)


# ---------------- GESTIONE DEGLI ERRORI

"""
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Pagina non trovata: ' + str(error)}), 404)


@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': 'Errore nella parte server: ' + str(error)}), 500)
"""


# ---------------- REST API

@nsv.route('/rest/parse')
@nsv.param('testo', 'il testo da parsare')
@nsv.response(HTTPStatus.OK, "Computation done")
# @app.route('/rest/parse', methods=['POST'])
class ParseRequest(Resource):

    def post(self):
        """
        Servizio di parsing di un contenuto
        :return:
        """
        if request.json and 'testo' in request.json:
            testo = request.json['testo']

            # TODO: rendere parametrico la possibilità di escludere AKN
            ret, xml, akn = parse_string(testo, build_akn=True)
            if ret == 0:
                return make_response(jsonify({'xml': xml, 'akn': akn, 'stderr': config.stdout_with_context}), 200)
            else:
                return make_response(jsonify({'error': 'errore ritornato nella esecuzione: ' + str(ret)}), 200)

        return make_response(jsonify({'error': 'La richiesta JSON non è ben formata: deve esserci il campo "testo"'}),
                             200)


@nsv.route('/rest/samples')
@nsv.response(HTTPStatus.OK, "Samples got")
# @app.route('/rest/samples')
class GetSamples(Resource):
    """
    Ritorna la lista dei documenti di esempio su cui effettuare il parsing
    :return:
    """

    def get(self):

        path_in = 'web/static/txt'
        files = []
        if os.path.isdir(path_in):
            p = Path(path_in).glob('./*.txt')
            files.extend([x for x in p if x.is_file()])
        else:
            files.append(Path(path_in))

        l = [os.path.basename(r"./" + str(f)) for f in files]
        l.sort()
        return make_response(jsonify({'samples': l}), 200)


# ---------------- MAIN

# def log_uncaught_exceptions(ex_cls, ex, tb):
#     app.logger.critical(''.join(traceback.format_tb(tb)))
#     app.logger.critical('{0}: {1}'.format(ex_cls, ex))

if __name__ == '__main__':

    logHandler = set_log(logging.DEBUG, noterminal=False)

    # configurazione del logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(logHandler)
    # sys.excepthook = log_uncaught_exceptions

    try:

        env = os.environ['ENV']
        server_port = os.environ['SERVER_PORT']
        if env == 'development':
            """
            Web server per lo sviluppo
            """
            # app.run(debug=True, host="0.0.0.0", port=5000, threaded = True, ssl_context=context)
            app.run(debug=False, host="0.0.0.0", port=server_port, threaded=True)
        elif env == 'production':
            """
            Utilizzo un server web con interfaccia WSGI (gevent ma si potrebbe anche mod_wsgi per Apache
            """
            http_server = WSGIServer(('', 5000), app)
            http_server.serve_forever()
        else:
            app.logger.critical(f"Nessun ambiente di esecuzione impostato (ENV={env})")

    except Exception as e:
        app.logger.critical(e)
