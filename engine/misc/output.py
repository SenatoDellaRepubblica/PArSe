

import logging
import sys
import config

logger = logging.getLogger()

def print_out(text):
    """
    Stampa in Stdout
    :param text:
    :return:
    """
    print(text, file=sys.stdout)
    config.stdout += text
    # config.stdout = ''.join((config.stdout,text))


def print_out_and_log(text):
    """
    Stampa in Stdout a mette nel log
    :param text:
    :return:
    """

    # elimina i new line e vi sostituisce un PIPE per aumentare la leggibilità dei file di log
    text = text.replace('\n','|').replace('\r','|')

    print(config.std_context.ljust(config.LOG_LJUST,'.') + text, file=sys.stdout)
    config.stdout_with_context += config.std_context.ljust(config.LOG_LJUST, '.') + text + "\n"
    logger.info(config.std_context.ljust(config.LOG_LJUST, '.') + text)

def set_err_context(context: str):
    """
    Imposta il contesto d'errore inserendo un prefisso stringa nella linea inviata in stderr
    :param context:
    :return:
    """
    config.std_context = '[' + context + ']'

def init_vars():
    """
    Inizializza le variabili per gli std...
    :return:
    """
    config.stdout = ''
    config.stdout_with_context = ''
    config.std_context = ''
