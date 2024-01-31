import re
from io import StringIO
from subprocess import Popen, PIPE

import logging

from bs4 import BeautifulSoup

from config import ANTIWORD
from engine.misc.docx_mgr import get_docx_text
from engine.misc.output import print_out_and_log
from engine.misc.tika_converter import tika_convert

logger = logging.getLogger(__name__)

try:
    from docx import Document
except ImportError:
    print_out_and_log('Modulo Python DOCX non disponibile')

# http://stackoverflow.com/questions/5725278/python-help-using-pdfminer-as-a-library

try:
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage
except ImportError:
    print_out_and_log('Modulo Python pdfminer non disponibile')


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    txt = retstr.getvalue()
    retstr.close()
    return txt


def tika_conv_to_text(file_path: str):
    """
    Converte il documento utilizzando tika
    :param file_path: 
    :return: 
    """
    output_text, error = tika_convert(file_path)
    if len(error) > 0:
        logger.error(f"Errore nella conversione del documento {file_path}: {error}")
    return output_text


def document_to_text(ext, file_path):
    """
    Funzione di conversione generale

    :param ext:
    :param file_path:
    :return:
    """

    def conv_with_tika(f_path):
        print_out_and_log('Problema nella esecuzione di ANTIWORD, provo con TIKA la conversione dei DOC')
        logger.info("Conversione con TIKA: DOC")
        return tika_conv_to_text(f_path)

    if ext == ".doc":
        # return tika_conv_to_text(file_path)
        logger.info("Conversione DOC con ANTIWORD")
        # mettere nella root del disco
        cmd = [ANTIWORD, file_path]
        try:
            p = Popen(cmd, stdout=PIPE)
            stdout, stderr = p.communicate()
            return_code = p.returncode
            if return_code == 0:
                return stdout.decode('ascii', 'ignore')
            else:
                return conv_with_tika(file_path)
        except FileNotFoundError:
            return conv_with_tika(file_path)
    elif ext == ".pdf":
        logger.info("Conversione PDF con PDFMINER")
        return convert_pdf_to_txt(file_path)

    # TIKA Converter
    elif ext == ".docx" or ext == ".odt" or ext.startswith(".htm"):
        logger.info(f"Conversione con TIKA: {ext}")
        return tika_conv_to_text(file_path)


SOPPRESSO_LEMMA = "soppress"
IDENTICO_LEMMA = "identic"


def taf_to_normal_form(html2parse: str) -> tuple[str, str]:
    """
    Function to transform TAF (Testo a Fronte) in a normal form
    :param html2parse
    :return (html, txt)
    """

    soup = BeautifulSoup(html2parse, 'html.parser')
    id_list = soup.select("#presentazionetaf")

    if len(id_list) == 1 and id_list[0] is not None:

        # elimino i newline all'interno dei tag TD
        for element in soup.find_all('td'):
            new_content = BeautifulSoup(str(element).replace('\n',''), features="lxml")
            element.replace_with(new_content)

        # modifica la tabella a seconda di come sono impostati
        # gli Identici e i Soppressi
        tr_list = id_list[0].find_all('tr')
        for tr in tr_list:
            td1, td2 = tr.find_all("td")

            # TODO: cambiare la logica dell'Identico: restando NON case sensitive, se a destra si trova (?<INCIPIT>.*?)Identic([aio]|he), il contenuto del gruppo incipit deve corrispondere all'inizio della cella di sinistra. Ex. 808-A della 19a
            # logica per costruire il consolidato
            if (("%s" % IDENTICO_LEMMA) in td2.text.lower() and len(td2.text) < len(IDENTICO_LEMMA) + 10) or len(
                    td2.text.strip()) == 0:
                td2.replace_with(td1)
            elif ("%s" % SOPPRESSO_LEMMA) in td2.text.lower() and len(td2.text) < len(SOPPRESSO_LEMMA) + 10:
                td1.extract()
                td2.extract()
            else:
                td1.extract()

            tr.append('\n')

        # elimina la struttura della tabella e sostituisce con dei <div>
        tag_list = ['table', 'tr', 'td']
        for s in tag_list:
            for i in id_list[0].find_all(s):
                i.name = 'div'

        print(f"Testo consolidato: {str(soup)}")
        print(f"Testo piatto: {soup.get_text()}")

    return str(soup), soup.get_text()
