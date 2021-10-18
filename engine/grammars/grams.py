
from abc import ABCMeta, abstractmethod
from enum import Enum

# Infinito
import sys

import logging

logger = logging.getLogger(__name__)

INFINITE = sys.maxsize


class TK_ATTR(Enum):
    """
    Attributi per ogni Token
    """

    # priorità del token
    POS: str = "pos",

    # espressione di ricerca
    REGEX: str = "regex",

    # stringa con sostituzione
    REPL_S: str = "repl_s",

    # chiusura
    REPL_C: str = "repl_c"


# Grammatica Regolare: espressioni regolare e precedenza tra le espressioni

class TK_EN(Enum):
    """
    Enumerazione dei token
    """
    TITOLO: str = "titolo",
    CAPO: str = "capo",
    CAPO_RUBRICA: str = "capo_rubrica",
    ART: str = "art",
    ART_RUBRICA: str = "art_rubrica",
    COMM: str = "comm",
    LET: str = "let",
    NUM: str = "num",
    NOV: str = "novella"


class Stato(object):
    """
    Definisce uno stato dell'Automa
    """

    def __init__(self, tipo_stato, mul=1):
        """
        Costruttore della classe
        :param tipo_stato: Tipologia dello stato (TK_EN)
        :param mul: molteplicità dello stato
        """
        self.tk_type = tipo_stato
        self.trans = []
        self.parent = None
        self.mul = mul

    def __repr__(self):
        return str(self.tk_type)

    def __str__(self):
        return self.__repr__()

    def goto(self, stato_or_stato_list):
        """
        Aggiunge uno stato di destinazione per la costruzione dell'Automa
        :param stato_or_stato_list:
        :return:
        """

        if type(stato_or_stato_list) is list:
            for s in stato_or_stato_list:
                if type(s) is Stato:
                    self.trans.append(s)
                    s.parent = self
        elif type(stato_or_stato_list) is Stato:
            self.trans.append(stato_or_stato_list)
            stato_or_stato_list.parent = self

        return self


class StatoStart(Stato):
    """
    Stato iniziale dell'automa
    """

    def __init__(self):
        super().__init__(None)

    def __repr__(self):
        return 'S'

    def __str__(self):
        return self.__repr__()


class StatoEnd(Stato):
    """
    Stato finale dell'automa
    """

    def __init__(self):
        super().__init__(None)

    def __repr__(self):
        return 'E'

    def __str__(self):
        return self.__repr__()


class Transizione(object):
    """
    Indica una transizione nella visita dell'automa di parsing
    """

    def __init__(self, stato_dst: Stato, txt_post: str, rep: str = '', chiusura: str = '', txt_pre: str = ''):
        self.rep = rep
        self.chiusura = chiusura
        self.txt_post = txt_post
        self.stato_dst = stato_dst
        self.txt_pre = txt_pre

    def __repr__(self):
        return f'{str(self.stato_dst)}: {str(self.rep)}'

    def __str__(self):
        return self.__repr__()


# ***************************************************

class GramForParser(metaclass=ABCMeta):
    """
    Classe astratta delle grammatiche
    """

    # Strutture a supporto
    grm_tk_dic = None

    # Costanti per la sintassi
    FLAGS = None

    # Parte di contenuto riconosciuta dalla grammatica
    CPART = None

    # Parte sinistra consumata
    SPART = None

    # Parte da sostituire a CPART
    REPL_CPART = None

    # Stati dell'Automa
    S = StatoStart()  # inizializzazione inutile se lo si fa nella sottoclasse
    E = StatoEnd()  # inizializzazione inutile se lo si fa nella sottoclasse

    @staticmethod
    @abstractmethod
    def get_higher_state() -> Stato:
        """
        Ottiene lo stato più elevato
        """
        pass

    @staticmethod
    @abstractmethod
    def get_automata() -> Stato:
        """
        Ottiene l'automa
        """
        pass
