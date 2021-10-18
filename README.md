# PArSe: Parser Articolato Senato #

[![License](https://img.shields.io/badge/license-GPL3-green)](https://.../LICENSE)
[![Build](https://img.shields.io/badge/build-1.1-yellowgreen)](https://github.com/SenatoDellaRepubblica/PArSe)

PArSe è un parser del solo articolato dei progetti o disegni di legge parlamentari.
Sviluppato dal Servizio dell'Informatica del Senato della Repubblica.

## Getting started ##

Per eseguire il parser:

1. Assicurarsi di aver installato Python 3.9
2. Checkout del progetto
    `git clone https://github.com/SenatoDellaRepubblica/PArSe.git && cd PArSe`
3. Installazione delle librerire richieste mediante pip per Python3
    `pip3 install -r requirements.txt`
4. Per eseguire l'interfaccia Web
    `python3 parse_web.py`
5. Per eseguire il parser a riga di comando
   `python3 parse_cli.py -h`

## Librerie esterne ##

Per la trasformazione di documenti PArSe utilizza Antiword per i .DOC e Tika per i .DOCX. 

Nel progetto non sono presenti i compilati dei due prodotti. Per Tika è necessario il runtime Java.

## Autore ##

Senato della Repubblica - Servizio dell'Informatica

## Licenza ##

CC BY 3.0