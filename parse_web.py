import logging
import os
from http import HTTPStatus

from pathlib import Path

from colorama import Fore
from flask_cors import CORS
from flask_restx import Api, Resource
from gevent.pywsgi import WSGIServer

import config
from flask import Flask, Blueprint, Response, redirect
from flask import make_response, jsonify, send_from_directory, url_for
from flask import render_template_string

# impostazione di Flask
from flask import request

from engine.misc.output import print_out
from parse_cli import parse_string
from engine.misc.converter import taf_to_normal_form
from engine.misc.log import set_log

PRODUCTION = 'production'

DEVELOPMENT = 'development'

logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='web/static', static_url_path='/res')
app.root_path = os.path.dirname(os.path.abspath(__file__))

SWAGGER_UI_HTML = "swagger-ui"

CORS(app)
blueprint = Blueprint('api', __name__, url_prefix='/rest')

# Swagger
api = Api(blueprint,
          title="PArSe",
          description="Servizio per il parsing degli articolati di legge",
          contact="Roberto Battistoni",
          version=config.VERSION,
          contact_email="roberto.battistoni@senato.it",
          doc=f'/{SWAGGER_UI_HTML}/index.html')

app.register_blueprint(blueprint)
nsv = api.namespace('', description='Parser articolati')

@app.route('/')
def home():
    return redirect("/app")

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


# ---------------- REST API

@nsv.route('/untaf')
@nsv.param('testo', 'il testo da parsare')
@nsv.response(HTTPStatus.OK, "Taf Normalizer")
class UnTaf(Resource):
    """
    Ritorna il testo consolidato
    :return:
    """

    def post(self):
        html_text, _ = taf_to_normal_form(request.form.get("testo"))
        return make_response(html_text, 200)


@nsv.route('/parse')
@nsv.param('testo', 'il testo da parsare')
@nsv.response(HTTPStatus.OK, "Computation done")
class ParseRequest(Resource):

    def post(self):
        """
        Servizio di parsing di un contenuto
        :return:
        """
        if request.json and 'testo' in request.json:

            # TODO: prevedere un minimo di sanitizzazione...
            testo = request.json['testo']

            # TODO: rendere parametrico la possibilità di escludere AKN
            ret, xml, akn = parse_string(testo, build_akn=True)
            if ret == 0:
                return make_response(jsonify({'xml': xml, 'akn': akn, 'stderr': config.stdout_with_context}), 200)
            else:
                return make_response(jsonify({'error': 'errore ritornato nella esecuzione: ' + str(ret)}), 200)

        return make_response(jsonify({'error': 'La richiesta JSON non è ben formata: deve esserci il campo "testo"'}),
                             200)


@nsv.route('/samples')
@nsv.response(HTTPStatus.OK, "Samples got")
class GetSamples(Resource):
    """
    Ritorna la lista dei documenti di esempio su cui effettuare il parsing
    :return:
    """

    def get(self):

        try:
            env = os.environ['ENV']
        except KeyError as e:
            app.logger.critical(f'La variabile di ambiente {e} non esiste.')

        path_in = 'web/static/txt'
        if env != DEVELOPMENT:
            path_in = 'web/static/txt_prod'

        files = []
        if os.path.isdir(path_in):
            types = ('*.txt', '*.html', '*.htm')
            for t in types:
                p = Path(path_in).glob(t)
                files.extend([x for x in p if x.is_file()])
        else:
            files.append(Path(path_in))

        l = [os.path.basename(r"./" + str(f)) for f in files]
        l.sort()
        return make_response(jsonify({'samples': l}), 200)


if __name__ == '__main__':

    # Per prima cosa stampa il logo con la versione
    print_out(Fore.YELLOW + config.logo + Fore.RESET)

    logHandler = set_log(logging.DEBUG, noterminal=False)

    # configurazione del logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(logHandler)
    # sys.excepthook = log_uncaught_exceptions

    try:

        env = os.environ['ENV']
        server_port = os.environ['SERVER_PORT']

        if env == DEVELOPMENT:
            """
            Web server per lo sviluppo
            """
            # app.run(debug=True, host="0.0.0.0", port=5000, threaded = True, ssl_context=context)
            app.run(debug=False, host="0.0.0.0", port=int(server_port), threaded=True)
        elif env == PRODUCTION:
            """
            Utilizzo un server web con interfaccia WSGI (gevent ma si potrebbe anche mod_wsgi per Apache
            """
            http_server = WSGIServer(('0.0.0.0', int(server_port)), app)
            http_server.serve_forever()
        else:
            app.logger.critical(f"Nessun ambiente di esecuzione impostato (ENV={env})")

    except KeyError as e:
        app.logger.critical(f'La variabile di ambiente {e} non esiste.')
        quit(1)
