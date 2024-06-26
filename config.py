import os
import logging
import sys

sys.setrecursionlimit(10 ** 6)

VERSION = "1.3.8.1"

logo = fr"""
    ____  ___         _____   
   / __ \/   |  _____/ ___/___ 
  / /_/ / /| | / ___/\__ \/ _ \
 / ____/ ___ |/ /   ___/ /  __/
/_/   /_/  |_/_/   /____/\___/ 
   Parser Articolato Senato

PArSe - v. {VERSION}
"""

usage_sample = fr"""
uso: parse_cli.py
< legge da STDIN
> scrive su STDOUT
[-i <input file o directory>]   : file di input
[-o <output dir>]               : directory di output (opzionale)
[-h]                            : print this help

Esempi di invocazione:

-i c:\mydir\ -o c:\outdir\
-i c:\mydir\myfile.txt -o c:\outdir
-o c:\outdir < type c:\articolato.txt 
-i c:\mydir\articolato.txt > c:\articolato.txt
"""

# Configurazione dei log

LOG_LEVEL = logging.INFO
LOG_LJUST = 12
LOG_PATH = './log/'

# variabili globali che memorizzano lo standard output e lo standard error del parser

# indica se l'output va anche al terminale
stdout = ''
stdout_with_context = ''
std_context = ''

# contesto degli errori o warning da ritornare al chiamante

context_messages = dict()
context_messages['warnings'] = list()
context_messages['errors'] = list()

# path del convertitore per DOC
ANTIWORD = './bin/antiword/antiword'

# path vari

UNITTEST_PATH_IN = '../test/dataset/in/all'
UNITTEST_PATH_OUT = '../test/unittest/dataset/expected'
UNITTEST_PATH_DIFF = '../test/unittest/dataset/diff'
UNITTEST_PATH_WORK = '../test/unittest/dataset/work'

# ---------------- Max e Min del Parser

# soglia massima di ricorsione
SOGLIA_MAX_RICORSIONE = 0  # 0 per infinito

# soglia massima delle chiusure
SOGLIA_CHIUSURE = 1_000

# impostazione per l'articolato
MARKER_INIZIO_ARTICOLATO = {
    "ddl": r"^\s*?(?:Disegno|Progetto|Proposta)\s+?di\s+?Legge.*$",
    "decretoLegge": r"E\s*m\s*a\s*n\s*a\W+il\sseguente\sdecreto-legge"
}
PRE_TAG = '@@@PRE@@@'

# impostazioni per il debug
DEBUG = True
DEBUG_ESTESO = True

# Saxon transformer per Akoma Ntoso version

_akntranserv_url = os.getenv('AKNSERV-URL')
REST_SAXON = _akntranserv_url


