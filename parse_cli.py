

import getopt
import logging
import os
import sys
from pathlib import Path

import config
from config import MARKER_INIZIO_ARTICOLATO
from engine.grammars.articolato.gram_art_novella import GramArticolatoInNovella as GAN
from engine.grammars.articolato.gram_articolato import GramArticolato as GA
from engine.exceptions import ParserException
from engine.formatter.akn import inxml2akn
from engine.misc.converter import document_to_text
from engine.misc.log import set_log, log_uncaught_exceptions
from engine.misc.misc import sub_special_chars, read_text_with_enc, check_cvs_in_path, \
    del_and_make_dir
from engine.misc.output import print_out, print_out_and_log, init_vars, set_err_context
from engine.parser.parser_articolato import ParserArticolato


def parse_files(path_in: str, path_out: str = ''):
    """
    processa i file e li parserizza
    :param path_in:
    :param path_out:
    :return:
    """

    FILES_PROC = 'Dir'
    set_err_context(FILES_PROC)
    print_out_and_log("**** START PARSING DIR ****")
    files = []
    if os.path.isdir(path_in):
        p = Path(path_in).glob('./**/*')
        files.extend([x for x in p if x.is_file()])
    else:
        files.append(Path(path_in))

    del_and_make_dir(path_out)

    # esegue il parsing dei file
    ret = 0
    for f in files:
        # piccolo hack per escludere le cartelle CVS
        if check_cvs_in_path(str(f)):
            continue

        full_file_name = r"./" + str(f)
        if config.DEBUG:
            print_out_and_log("==> " + full_file_name)
        ext = f.suffix

        try:
            if ext == '.txt':
                ddl_text = read_text_with_enc(full_file_name)
            elif ext == '.docx':
                ddl_text = document_to_text(ext, full_file_name)
            elif ext == '.doc':
                ddl_text = document_to_text(ext, full_file_name)
            elif ext == '.pdf':
                ddl_text = document_to_text(ext, full_file_name)
            else:
                print_out_and_log("File extension not recognized!")
                ret = ret or 1
                continue
        except FileNotFoundError:
            print_out_and_log('FileNotFoundError exception, jump the file')
            continue

        ret = parse_string(ddl_text, path_out, os.path.basename(full_file_name), build_akn=True, ret=ret)
        set_err_context(FILES_PROC)

    print_out_and_log("**** END PARSING DIR ****")
    return ret


def parse_string(txt2parse: str, path_out: str = '', out_file_name: str = '', build_akn: bool = False, ret: int = 0):
    """
    Esegue il parsing di un testo in formato stringa

    :param build_akn:
    :param txt2parse:
    :param out_file_name:
    :param path_out:
    :param ret:
    :return:
    """

    init_vars()
    STRING_PROC = 'Txt_Norm'
    set_err_context(STRING_PROC)
    print_out_and_log("=======> Start String Parsing... <======")
    txt2parse = sub_special_chars(txt2parse)

    # ====>>>>>>> esegue il parsing del testo
    pa = ParserArticolato(GA, GAN)
    try:
        ret_akn, akn = None, None
        set_err_context('Parse')
        ret_xml = pa.execute(txt2parse, MARKER_INIZIO_ARTICOLATO, parse_novelle=True)
        if build_akn:
            set_err_context("AKN_Conv")
            ret_akn, akn, log = inxml2akn(ret_xml)



        set_err_context(STRING_PROC)

        # Se è dato un path scrive su disco
        if len(path_out) > 0:
            out_path = path_out + '/' + out_file_name
            # scrive il file TXT originale
            with open(out_path + '.txt', mode='w', encoding='utf-8') as file:
                file.write(txt2parse)
            # scrive il file XML ottenuto dalla trasformazione
            with open(out_path + '.xml', mode='w', encoding='utf-8') as file:
                file.write(ret_xml)

            if ret_akn:
                # scrive il file AKN ottenuto dalla trasformazione
                with open(out_path + '.akn.xml', mode='w', encoding='utf-8') as file:
                    file.write(akn)
            else:
                print_out_and_log("Problema durante la trasformazione AKN!")

            return ret
        else:
            print_out(ret_xml)
            return ret, ret_xml, akn

    except ParserException as e:
        print_out_and_log(f"Parsing Exception: {e}")
        ret = ret or 1
        return ret
    finally:
        print_out_and_log("=======> End String Parsing <======")


def main(argv):
    """
    Main process

    :param argv:
    :return:
    """



    try:
        opts, args = getopt.getopt(argv, "hi:o:")
    except getopt.GetoptError:
        print_out_and_log('Controllare gli argomenti')
        print_out(config.usage_sample)
        sys.exit(2)

    # Per prima cosa stampa il logo con la versione
    print_out(config.logo)

    path_input = None
    dir_output = None
    for opt, arg in opts:
        if opt == '-h':
            print_out(config.usage_sample)
            return 1
        elif opt == "-i":
            path_input = arg
        elif opt == "-o":
            dir_output = arg

    if path_input:
        if dir_output:
            ret = parse_files(path_input, dir_output)
            return ret
        else:
            ret = parse_files(path_input)
            return ret
    elif dir_output:
        if not path_input:
            ret = parse_string(sys.stdin.read(), dir_output, 'out.xml', build_akn=True)
            return ret
    else:
        print_out_and_log('Sto leggendo da STDIN...')
        ret = parse_string(sys.stdin.read())
        return ret


if __name__ == '__main__':
    set_log(config.LOG_LEVEL)
    #sys.excepthook = log_uncaught_exceptions
    ret = main(sys.argv[1:])
    sys.exit(ret)
