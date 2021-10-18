
import re

from jinja2 import Environment
from jinja2 import FileSystemLoader
import logging

logger = logging.getLogger(__name__)


def art_in_senxml_tpl(incipit_articolato: str, articolato: str, prefazione: str) -> str:
    """
    Inserisce l'articolato all'interno del template per il SenXML
    :param incipit_articolato:
    :param prefazione:
    :param articolato:
    :return:
    """
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('engine/template/static/ddlpres/ddlpres.tpl.xml')

    xml = template.render(incipit_articolato=incipit_articolato, articolato=articolato, prefazione=prefazione)

    # Aggiunge per alcuni elementi gli attributi inIndice="" e idPart=""

    elements = ['a:Capo', 'a:Articolo']
    rep_ptrn = r'\g<1> idPart="" inIndice="">'
    for ele in elements:
        pattern = fr'(<{ele})>'
        xml = re.sub(pattern, rep_ptrn, xml, flags=re.IGNORECASE)

    return xml
