

from typing import Tuple

import requests

from config import REST_SAXON
from engine.misc.output import print_out_and_log


def inxml2akn(xml: str) -> Tuple[bool, any, any]:
    url = REST_SAXON
    if url:
        files = {'file_xml': xml,
                 'file_xslt': open("./engine/formatter/DDL2Akoma.xsl", 'rb')}

        print_out_and_log(f"Trasformazione XSLT per formato Akoma Ntoso")
        try:
            res = requests.post(url, files=files, timeout=10) # 10 secondi di timeout
            print_out_and_log(f"Log Trasformazione: {res.json()['log']}")
            return (True, res.json()['xml'], res.json()['log']) if res.status_code == 200 else (False, "", "")
        except requests.exceptions.ConnectionError:
            print_out_and_log(f"Errore di connessione al server '{url}' per la conversione AKN")
            return False, "", ""
        except requests.exceptions.InvalidURL:
            print_out_and_log(f"URL '{url}' non valida")
            return False, "", ""
        except KeyError:
            return False, "", ""

    msg = f"@Trasformatore non invocato per la url: {url}"
    print_out_and_log(msg)
    return True, msg, ""
