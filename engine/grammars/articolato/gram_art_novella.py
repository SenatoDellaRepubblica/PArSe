import logging

from engine.grammars.articolato.gram_articolato import GramArticolato as GA
from engine.grammars.grams import StatoStart, Stato, TK_EN, TK_ATTR
from copy import deepcopy

logger = logging.getLogger(__name__)


class GramArticolatoInNovella(GA):
    """
    La grammatica dell'Articolato dentro la Novella
    """

    # espressioni regolari
    REGEX_CAPO = fr'^\s*?(?P<{GA.SPART}>(capo)\s*(?P<{GA.CPART}>[IVX]+))'
    REGEX_ARTICOLO = fr'^\s*?(?P<{GA.SPART}>(art\.?|articolo\.?)\s*(?P<{GA.CPART}>{GA._INT_REGEX_NUM})\.?)'
    # REGEX_RUBR_ART = r'(?P<SPART>[ ]+?[–-]{1,2}?[ ]+?\((?P<CPART>.+?)\).*?[–-]{1,2})'
    REGEX_RUBR_ART = fr'(?P<{GA.SPART}>[ –-]*?\((?P<{GA.CPART}>.+?)\)\.?[ –-]*)'
    REGEX_COMMA = fr'(?:^\s*|[ ]+?[–-]{{1,2}}[ ]+?)(?P<{GA.SPART}>(?P<{GA.CPART}>{GA._INT_REGEX_NUM})[.]\s+)'

    # crea una copia della dictionary
    grm_tk_dic = deepcopy(GA.grm_tk_dic)

    # regole di tokenizzazione cambiate
    grm_tk_dic[TK_EN.CAPO][TK_ATTR.REGEX] = REGEX_CAPO
    grm_tk_dic[TK_EN.ART][TK_ATTR.REGEX] = REGEX_ARTICOLO
    grm_tk_dic[TK_EN.ART_RUBRICA][TK_ATTR.REGEX] = REGEX_RUBR_ART
    grm_tk_dic[TK_EN.COMM][TK_ATTR.REGEX] = REGEX_COMMA

    """    
       Sintassi in BNF: eredita la BNF della grammatica dell'articolato. Cambia solo la produzione da S

       Stato            | Produzioni 
       -----------------|-------------------------------------------------------------------------------------
                        | Fase discendente                 | Fase ascendente
       -----------------|-------------------------------------------------------------------------------------                                                 
       S               := Capo | Articolo | Comma | Lettera 
       ------------------------------------------------------------------------------------------------------    
    """

    # Definizione del DFA
    S = StatoStart()  # deve essere inzializzato qui

    # Variazione della grammatica
    S.goto([GA.S_Capo, GA.S_Art, GA.S_Comm, GA.S_Let])

    @staticmethod
    def get_automata() -> Stato:
        return GramArticolatoInNovella.S
