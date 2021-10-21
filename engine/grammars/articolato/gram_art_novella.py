

import logging

from engine.grammars.articolato.gram_articolato import GramArticolato as GA
from engine.grammars.grams import StatoStart, Stato, TK_EN, TK_ATTR

logger = logging.getLogger(__name__)


class GramArticolatoInNovella(GA):
    """
    La grammatica dell'Articolato dentro la Novella
    """

    # espressioni regolari
    REGEX_CAPO = r'^\s*?(?P<SPART>(capo)\s*(?P<CPART>[IVX]+))'
    REGEX_ARTICOLO = fr'^\s*?(?P<SPART>(art\.?|articolo\.?)\s*(?P<CPART>{GA._INT_REGEX_NUM})\.?)'
    # REGEX_RUBR_ART = r'(?P<SPART>[ ]+?[–-]{1,2}?[ ]+?\((?P<CPART>.+?)\).*?[–-]{1,2})'
    REGEX_RUBR_ART = r'(?P<SPART>[ –-]*?\((?P<CPART>.+?)\)\.?[ –-]*)'
    REGEX_COMMA = fr'(?:^\s*|[ ]+?[–-]{{1,2}}[ ]+?)(?P<SPART>(?P<CPART>{GA._INT_REGEX_NUM})[.]\s+)'

    # dictionary delle regole di tokenizzazione: copiato ma alcuni referenziano la classe parent
    grm_tk_dic = {

        TK_EN.TITOLO: {
            TK_ATTR.POS: 10,
            TK_ATTR.REGEX: GA.REGEX_TITOLO,
            TK_ATTR.REPL_S: f"<a:TitoloAtto>{GA.REPL_CPART}",
            TK_ATTR.REPL_C: '</a:TitoloAtto>\n'
        },
        TK_EN.CAPO: {
            TK_ATTR.POS: 20,
            TK_ATTR.REGEX: REGEX_CAPO,
            TK_ATTR.REPL_S: f'<a:Capo>\n<a:Num numero="{GA.REPL_CPART}"/>',
            TK_ATTR.REPL_C: '</a:Capo>\n'
        },
        TK_EN.CAPO_RUBRICA: {
            TK_ATTR.POS: 21,
            TK_ATTR.REGEX: GA.REGEX_RUBR_CAPO,
            TK_ATTR.REPL_S: f'<a:Rubrica>{GA.REPL_CPART}</a:Rubrica>',
            TK_ATTR.REPL_C: None
        },
        TK_EN.ART: {
            TK_ATTR.POS: 30,
            TK_ATTR.REGEX: REGEX_ARTICOLO,
            TK_ATTR.REPL_S: f'<a:Articolo>\n<a:Num numero="{GA.REPL_CPART}"/>',
            TK_ATTR.REPL_C: '</a:Articolo>\n'
        },
        TK_EN.ART_RUBRICA: {
            TK_ATTR.POS: 31,
            TK_ATTR.REGEX: REGEX_RUBR_ART,
            TK_ATTR.REPL_S: f'<a:Rubrica>({GA.REPL_CPART})</a:Rubrica>',
            TK_ATTR.REPL_C: None
        },
        TK_EN.COMM: {
            TK_ATTR.POS: 40,
            TK_ATTR.REGEX: REGEX_COMMA,
            TK_ATTR.REPL_S: f'<a:Comma>\n<a:Num numero="{GA.REPL_CPART}"/>',
            TK_ATTR.REPL_C: '</a:Comma>\n'
        },
        TK_EN.LET: {
            TK_ATTR.POS: 50,
            TK_ATTR.REGEX: GA.REGEX_LETTERA,
            TK_ATTR.REPL_S: f'<a:Lettera>\n<a:Num numero="{GA.REPL_CPART}"/>',
            TK_ATTR.REPL_C: '</a:Lettera>\n'
        },
        TK_EN.NUM: {
            TK_ATTR.POS: 60,
            TK_ATTR.REGEX: GA.REGEX_NUMERO,
            TK_ATTR.REPL_S: f'<a:Numero>\n<a:Num numero="{GA.REPL_CPART}"/>',
            TK_ATTR.REPL_C: '</a:Numero>\n'
        },
        TK_EN.NOV: {
            TK_ATTR.POS: 999,
            TK_ATTR.REGEX: GA.REGEX_NOVELLA,
            TK_ATTR.REPL_S: f"<{GA.TOKEN_NOVELLA}>{GA.REPL_CPART}</{GA.TOKEN_NOVELLA}>",
            TK_ATTR.REPL_C: None
        }
    }

    """    
       Sintassi in BNF: eredita dalla BNF della grammatica dell'articolato

       Stato            | Produzioni 
       -----------------|-------------------------------------------------------------------------------------
                        | Fase discendente                 | Fase ascendente
       -----------------|-------------------------------------------------------------------------------------                                                 
       S               := Capo | Articolo | Comma | Lettera 
       Capo            := Rubrica_Capo | Articolo
       Articolo        := Rubrica_Art | Comma              | Capo | E 
       Comma           := Novella | Lettera                | Capo | Articolo | E
       Lettera         := Novella | Numero                 | Capo | Articolo | Comma | E

       ------------------------------------------------------------------------------------------------------    
    """

    # Definizione del DFA
    S = StatoStart()  # deve essere inzializzato qui
    S_Capo = GA.S_Capo
    S_Art = GA.S_Art
    S_Comm = GA.S_Comm
    S_Let = GA.S_Let

    # Variazione della grammatica
    S.goto([S_Capo, S_Art, S_Comm, S_Let])

    @staticmethod
    def get_automata() -> Stato:
        return GramArticolatoInNovella.S
