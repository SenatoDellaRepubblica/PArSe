import os
import shutil
import subprocess

from pprint import pprint
from pyexpat import ExpatError
from xml.dom import minidom

import chardet
import time

import re

from engine.misc.output import print_out_and_log
from engine.grammars.grams import Stato
from engine.grammars.articolato.gram_articolato import GramArticolato as GA
import logging

logger = logging.getLogger(__name__)

"""
class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL, seconds)  # used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator
"""


def run_command(command_line):
    """
    Esegue una riga di comando in un nuovo processo

    :param command_line:
    :return: CompletedProcess
    """
    timeout = 3600
    ret = subprocess.run(command_line, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         timeout=timeout)
    return ret


def check_cvs_in_path(path: str):
    """
    Restituisce true se il path contiene la cartella CVS
    :param path:
    :return:
    """
    m = re.search(r'([\\/]CVS|[\\/]\\\.])', path, flags=re.I)
    return m


def del_and_make_dir(path_out: str):
    """
    Cancella e ricrea una directory

    :param path_out:
    :return:
    """
    if len(path_out) > 0 and os.path.exists(path_out):
        shutil.rmtree(path_out, ignore_errors=False)
        print_out_and_log("=======> Wait for makedirs <======")
        time.sleep(1)
    os.makedirs(path_out)


def pretty_print_xml(ret_xml: str) -> str:
    """
    Formatta il file XML correttamente
    """

    try:
        xml = minidom.parseString(ret_xml)
        xml = xml.toprettyxml(indent='  ', newl='\r')

        # normalizzazione \r isolati
        xml = xml.replace("\n\r", "\n").replace('\r', '\n')

        # sostituisco ai &quot; i double quote perchè minidom fa questo encoding (e non si sa perché)
        xml = xml.replace("&quot;", '"')

        # elimino le righe vuote
        xml = "\n".join([line.replace('\r', '') for line in xml.split('\n') if line.strip()])
        return xml

    except ExpatError:
        logger.error("Pretty print error: malformed xml")
        return ret_xml


def sub_special_chars(xml: str) -> str:
    """
    Effettua l'escape dei caratteri speciali per l'XML
    :param xml:
    :return:
    """
    return xml.replace("&", "&amp;") \
        .replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace('\f', '')


def read_text_with_enc(full_file_name: str, src_encoding: str = None) -> str:
    """
    Legge un file di testo con il corretto encoding

    :param src_encoding:
    :param full_file_name:
    :return:
    """

    m = re.search(r'\.enc_(?P<ENC>.+?)\.', full_file_name, flags=re.I)
    if m:
        src_encoding = m.group('ENC')

    # se non è impostato un encoding di partenza allora cerca di individuarlo leggendo il file
    if not src_encoding:
        enc = get_text_enc(full_file_name)
    else:
        enc = src_encoding

    try:
        with open(full_file_name, encoding=enc) as file:
            text = file.read()
    except UnicodeDecodeError:
        if src_encoding != 'iso-8859-1':
            print_out_and_log("UnicodeDecodeError: trying with ISO88591 ==> " + full_file_name)
            text = read_text_with_enc(full_file_name, src_encoding='iso-8859-1')
        elif src_encoding != 'cp1252':
            print_out_and_log("UnicodeDecodeError: trying with CP1252 ==> " + full_file_name)
            text = read_text_with_enc(full_file_name, src_encoding='cp1252')
        else:
            with open(full_file_name, encoding='utf-8') as file:
                text = file.read()

    return text


def get_text_enc(full_file_name):
    """
    Ottiene l'encoding di un file corrente

    :param full_file_name:
    :return:
    """
    # legge i dati in bytes
    with open(full_file_name, mode='rb') as file:
        rawdata = file.read()
    enc = chardet.detect(rawdata)['encoding']
    print_out_and_log("Detected Encoding is > " + enc)
    return enc


def show_automata(gram):
    """
    Visualizza l'automa
    :param gram:
    :return:
    """

    try:
        import networkx as nx
    except ImportError:
        print_out_and_log('Modulo NetworkX non disponibile')
        quit(1)

    try:
        import networkx_viewer
    except ImportError:
        print_out_and_log('Modulo NetworkX_Viewer non disponibile')
        quit(1)

    G = nx.MultiGraph()
    visited_list = []

    def build_graph(stato: Stato):
        """
        Funziona ricorsvia
        :param stato:
        :return:
        """
        if stato is not None:
            for s_dst in stato.trans:
                edge = (stato, s_dst)
                pprint(edge)
                G.add_edge(*edge)
                visited_list.append(stato)
                if s_dst is not gram.E and s_dst not in visited_list:
                    build_graph(s_dst)

    automata = gram.get_automata()
    build_graph(automata)
    app = networkx_viewer.Viewer(G)
    app.mainloop()


if __name__ == '__main__':
    show_automata(GA)
