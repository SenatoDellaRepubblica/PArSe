import re

from jinja2 import Environment
from jinja2 import FileSystemLoader
import logging

logger = logging.getLogger(__name__)


def art_in_senxml_tpl(tipo_testo: str, incipit_articolato: str, articolato: str, prefazione: str) -> str:
    """
    Inserisce l'articolato all'interno del template per il SenXML
    :param tipo_testo: ddlpres, ddlmess, ddelcomm, dl
    :param incipit_articolato:
    :param prefazione:
    :param articolato:
    :return:
    """
    env = Environment(loader=FileSystemLoader('.'))

    if tipo_testo in ['ddl']:
        template = env.get_template('engine/template/static/ddlpres/main.tpl.xml')
    elif tipo_testo in ['dl']:
        template = env.get_template('engine/template/static/dl/main.tpl.xml')
    else:
        raise Exception("Tipo testo non riconosciuto per il template Ninja2")

    xml = template.render(incipit_articolato=incipit_articolato, articolato=articolato, prefazione=prefazione)

    # Aggiunge per alcuni elementi gli attributi inIndice="" e idPart=""

    elements = ['a:Capo', 'a:Articolo']
    rep_ptrn = r'\g<1> idPart="" inIndice="">'
    for ele in elements:
        pattern = fr'(<{ele})>'
        xml = re.sub(pattern, rep_ptrn, xml, flags=re.IGNORECASE)

    return xml
