
import os
from pathlib import Path

import logging

import sys

import config
from parse_cli import parse_string
from engine.misc.converter import document_to_text
from engine.misc.log import set_log, log_uncaught_exceptions
from engine.misc.misc import read_text_with_enc, check_cvs_in_path, del_and_make_dir
from engine.misc.output import print_out_and_log, print_out


# Imposta il logger
WORK_XML = '.work.xml'
WORK_TXT = '.work.txt'
set_log(logging.INFO, 'unittest_log.txt')
sys.excepthook = log_uncaught_exceptions


def build_parsed_docs(path_in: str, exclude_extensions=None):
    """
    Costruisce i documenti in WORK per i successivi test
    :param exclude_extensions: estensioni da non considerare (con il punto iniziale)
    :param path_in:
    :return:
    """

    if exclude_extensions is None:
        exclude_extensions = []

    path_work = config.UNITTEST_PATH_WORK
    del_and_make_dir(path_work)

    files = []
    if os.path.isdir(path_in):
        p = Path(path_in).glob('./**/*')
        files.extend([x for x in p if x.is_file()])
    else:
        files.append(Path(path_in))

    # esegue il parsing dei file
    for f in files:
        # piccolo hack per escludere le cartelle CVS
        if check_cvs_in_path(str(f)):
            continue

        full_file_name = r"./" + str(f)
        nome_file = os.path.basename(full_file_name)
        try:
            if config.DEBUG:
                print_out_and_log("\n\n==> " + full_file_name)
            ext = f.suffix
            if ext in exclude_extensions:
                continue
            if ext == '.txt':
                ddl_text = read_text_with_enc(full_file_name)
            elif ext in ['.docx', '.doc', '.pdf']:
                ddl_text = document_to_text(ext, full_file_name)
            else:
                print_out_and_log("Estensione non riconosciuta")
                continue
        except FileNotFoundError:
            print_out_and_log('Eccezione FileNotFoundError, salto il file')
            continue

        if ddl_text:
            parse_and_write(ddl_text, nome_file)


def parse_and_write(ddl_text, nome_file):
    """
    Esegue il parse di un file e lo scrive su disco
    
    :param ddl_text: testo da parsare
    :param nome_file: nome del file da scrivere
    :return: 
    """
    parse_string(ddl_text)
    parsed_xml = config.stdout
    file_name = f'{config.UNITTEST_PATH_WORK}/{nome_file}{WORK_TXT}'
    with open(file_name, mode='w', encoding='utf-8') as file:
        file.write(ddl_text)
    file_name = f'{config.UNITTEST_PATH_WORK}/{nome_file}{WORK_XML}'
    with open(file_name, mode='w', encoding='utf-8') as file:
        file.write(parsed_xml)


# Inizializza i test creando i file in WORK
print_out("Inizializzazione dei Test: generazione dei file in WORK")
#build_parsed_docs(config.UNITTEST_PATH_IN, ['.doc'])
build_parsed_docs(config.UNITTEST_PATH_IN)


def get_parsed_docs():
    """
    Generator che restituisce i test parsati a partire dalla lista in path_in
    :return:
    """

    path_work = config.UNITTEST_PATH_WORK

    files_txt = []
    p = Path(path_work).glob(f'./**/*{WORK_TXT}')
    # ordinati per ordine lessicografico
    files_txt.extend([x for x in p if x.is_file()])
    files_txt.sort()

    files_xml = []
    p = Path(path_work).glob(f'./**/*{WORK_XML}')
    # ordinati per ordine lessicografico
    files_xml.extend([x for x in p if x.is_file()])
    files_xml.sort()

    files_names = [str(x).replace(WORK_TXT, "") for x in files_txt]
    # ordinati per ordine lessicografico
    files_names.sort()

    for f_xml, f_txt, f_name in zip(files_xml, files_txt, files_names):
        with f_xml.open(encoding='utf-8') as file:
            f_xml_content = file.read()

        with f_txt.open(encoding='utf-8') as file:
            f_txt_content = file.read()

        f_name_final = os.path.basename(f_name)
        yield f_xml_content, f_txt_content, f_name_final



