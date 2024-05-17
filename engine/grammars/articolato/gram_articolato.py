import re
from engine.grammars.grams import GramForParser, TK_ATTR, Stato, INFINITE, StatoStart, StatoEnd, TK_EN
import logging

logger = logging.getLogger(__name__)


class GramArticolato(GramForParser):
    """
    La grammatica per l'Articolato
    """

    # ############# PLACEHOLDER ################
    ALINEA = 'a:Alinea'
    CORPO = 'a:Corpo'
    TOKEN_NOVELLA = 'a:Novella'
    NS = 'a:'
    NUM = 'a:Num'
    RUBR = 'a:Rubrica'
    ART = 'a:Articolo'

    # ############## ATTENZIONE: SPART e CPART devono sempre esistere nelle espressioni regolari

    # nome del gruppo di cattura che identifica la parte da inserire
    CPART = 'CPART'
    # gruppo di cattura per eliminare caratteri al contorno della parte da inserire
    SPART = 'SPART'

    # placeholder con cui sostituire la parte catturata da CPART
    REPL_CPART = fr'\g<{CPART}>'

    # placeholder con cui sostituire la parte catturata da SPART: qualche volta va conservata come negli articoli, commi e numeri
    REPL_SPART = fr'\g<{SPART}>'

    _INT_REGEX_PREMISSIVI = r'0{0,5}'

    # regex che individua la parte numerica di: articoli e di commi e i numeri
    _INT_REGEX_NUM = fr'({_INT_REGEX_PREMISSIVI}\d+\-?\w*(\.\d+)*)'

    # *********************** Grammatica regolare per gli stati ************************

    # TODO: finire l'esclusione di capo
    EXCLUDE_CAPO = fr'(?=\s+(capo)\s{{,3}}[IVX]+)'

    EXCLUDE_ART = fr'(?=\s+(art\.?|articolo\.?)\s{{,3}}\d\.?)'

    # Particella: Titolo
    REGEX_TITOLO = fr'^\s*?(?P<{SPART}>(tit\.|titolo)\s*(?P<{CPART}>[IVX]+))\s*$'

    # Rubrica del Titolo
    REGEX_RUBR_TITOLO = fr'^(?P<{SPART}>\s+(?P<{CPART}>.+?({EXCLUDE_CAPO}|{EXCLUDE_ART})))'

    # Particella: Capo
    # aggiunto il match degli spazi bianchi fino a fine riga
    REGEX_CAPO = fr'^\s*?(?P<{SPART}>(capo)\s*(?P<{CPART}>[IVX]+))\s*$'

    # Rubrica del Capo
    # Nuova regex che esclude gli spazi prima e dopo la rubrica
    REGEX_RUBR_CAPO = fr'^(?P<{SPART}>\s+(?P<{CPART}>.+?{EXCLUDE_ART}))'

    # Particella: Articolo
    # aggiunto il match degli spazi bianchi fino a fine riga
    REGEX_ARTICOLO = fr'^\s*?(?P<{SPART}>(art\.?|articolo\.?)\s*(?P<{CPART}>{_INT_REGEX_NUM})\.?)\s*$'

    # Rubrica dell'articolo: dopo la parentesi matcha fino alla fine della riga (tolleriamo un . dopo la parentesi ma viene poi scartato come carattere)
    REGEX_RUBR_ART = fr'^\s*?(?P<{SPART}>\((?P<{CPART}>.+?)\)\.?)\s*$'

    # Particella: Comma
    REGEX_COMMA = fr'^\s*?(?P<{SPART}>(?P<{CPART}>{_INT_REGEX_NUM})[.]\s+)'

    # Particella: Lettera
    REGEX_LETTERA = fr'^\s*?(?P<{SPART}>(?P<{CPART}>{_INT_REGEX_PREMISSIVI}[a-zA-Z]\-?\w*)\)\s+)'

    # Particella: Numero
    REGEX_NUMERO = fr'^\s*?(?P<{SPART}>(?P<{CPART}>{_INT_REGEX_NUM})\)\s+)'

    # Novelle
    # REGEX_NOVELLA = fr'(?P<{SPART}>«(?P<{CPART}>.*?»\s*?[.;]?))'
    REGEX_NOVELLA = fr'(?P<{SPART}>«(?P<{CPART}>.*?)»\s*?[.;]?)'
    # matcha la novelle marcate: ATTENZIONE la parentesi esterna serve perché referenziate con gruppo 1 la CPART
    REGEX_NOVELLA_XML = fr'(<{TOKEN_NOVELLA}>(?P<{CPART}>.*?)</{TOKEN_NOVELLA}>)'

    # flags per le espressioni regolari
    FLAGS = re.MULTILINE | re.IGNORECASE | re.DOTALL

    # ################# SINTASSI DI TIPO CONTEXT FREE

    # Dizionario di supporto al parser con riferimento alle REGEX e ai replace da fare
    grm_tk_dic = {

        TK_EN.TITOLO: {
            TK_ATTR.POS: 40,
            TK_ATTR.REGEX: REGEX_TITOLO,
            TK_ATTR.REPL_S: f'<a:Titolo>\n<a:Num numero="{REPL_CPART}">{REPL_SPART}</a:Num>',
            TK_ATTR.REPL_C: '</a:Titolo>\n'
        },
        TK_EN.TITOLO_RUBRICA: {
            TK_ATTR.POS: 41,
            TK_ATTR.REGEX: REGEX_RUBR_TITOLO,
            TK_ATTR.REPL_S: f'<a:Rubrica>{REPL_CPART}</a:Rubrica>',
            TK_ATTR.REPL_C: None
        },
        TK_EN.CAPO: {
            TK_ATTR.POS: 50,
            TK_ATTR.REGEX: REGEX_CAPO,
            TK_ATTR.REPL_S: f'<a:Capo>\n<a:Num numero="{REPL_CPART}">{REPL_SPART}</a:Num>',
            TK_ATTR.REPL_C: '</a:Capo>\n'
        },
        TK_EN.CAPO_RUBRICA: {
            TK_ATTR.POS: 51,
            TK_ATTR.REGEX: REGEX_RUBR_CAPO,
            TK_ATTR.REPL_S: f'<a:Rubrica>{REPL_CPART}</a:Rubrica>',
            TK_ATTR.REPL_C: None
        },
        TK_EN.ART: {
            TK_ATTR.POS: 60,
            TK_ATTR.REGEX: REGEX_ARTICOLO,
            TK_ATTR.REPL_S: f'<a:Articolo>\n<a:Num numero="{REPL_CPART}">{REPL_SPART}</a:Num>',
            TK_ATTR.REPL_C: '</a:Articolo>\n'
        },
        TK_EN.ART_RUBRICA: {
            TK_ATTR.POS: 61,
            TK_ATTR.REGEX: REGEX_RUBR_ART,
            TK_ATTR.REPL_S: f'<a:Rubrica>({REPL_CPART})</a:Rubrica>',
            TK_ATTR.REPL_C: None
        },
        TK_EN.COMM: {
            TK_ATTR.POS: 70,
            TK_ATTR.REGEX: REGEX_COMMA,
            TK_ATTR.REPL_S: f'<a:Comma>\n<a:Num numero="{REPL_CPART}">{REPL_SPART}</a:Num>',
            TK_ATTR.REPL_C: '</a:Comma>\n'
        },
        TK_EN.LET: {
            TK_ATTR.POS: 80,
            TK_ATTR.REGEX: REGEX_LETTERA,
            TK_ATTR.REPL_S: f'<a:Lettera>\n<a:Num numero="{REPL_CPART}">{REPL_SPART}</a:Num>',
            TK_ATTR.REPL_C: '</a:Lettera>\n'
        },
        TK_EN.NUM: {
            TK_ATTR.POS: 90,
            TK_ATTR.REGEX: REGEX_NUMERO,
            TK_ATTR.REPL_S: f'<a:Numero>\n<a:Num numero="{REPL_CPART}">{REPL_SPART}</a:Num>',
            TK_ATTR.REPL_C: '</a:Numero>\n'
        },
        # ATTENZIONE: la novella è un elemento che deve conservare anche la chiusura, quindi viene considerato inline
        # TODO: implementare la logica con il riconoscimento dei caporali bilanciati
        TK_EN.NOV: {
            TK_ATTR.POS: 999,
            TK_ATTR.REGEX: REGEX_NOVELLA,
            TK_ATTR.REPL_S: f"<{TOKEN_NOVELLA}>{REPL_CPART}</{TOKEN_NOVELLA}>",
            TK_ATTR.REPL_C: None
        }
    }

    # Definizione degli stati del DFA

    S = StatoStart()
    S_Titolo = Stato(TK_EN.TITOLO)
    S_Titolo_Rubr = Stato(TK_EN.TITOLO_RUBRICA)
    S_Capo = Stato(TK_EN.CAPO)
    S_Capo_Rubr = Stato(TK_EN.CAPO_RUBRICA)

    # RB 06/06/2024: Aggiunta molteplicità infinita per il caso di articolati con commi non numerati in cui almeno riconosce gli articoli in sequenza
    S_Art = Stato(TK_EN.ART, INFINITE)
    S_Art_Rubr = Stato(TK_EN.ART_RUBRICA)
    S_Comm = Stato(TK_EN.COMM, INFINITE)
    S_Let = Stato(TK_EN.LET, INFINITE)
    S_Num = Stato(TK_EN.NUM, INFINITE)
    S_Nov = Stato(TK_EN.NOV, INFINITE)
    E = StatoEnd()

    """        
        Sintassi in BNF
    
        Stato            | Produzioni 
        -----------------|-------------------------------------------------------------------------------------
                         | Fase discendente                 | Fase ascendente
        -----------------|-------------------------------------------------------------------------------------                                                 
        S               := Titolo | Capo | Articolo
        Titolo          := Rubrica_Titolo | Capo | Articolo | E      
        Capo            := Rubrica_Capo | Articolo          | Titolo | E        
        Articolo        := Rubrica_Art | Comma              | Titolo | Capo | E                 
        Comma           := Novella | Lettera                | Titolo | Capo | Articolo | E
        Lettera         := Novella | Numero                 | Titolo | Capo | Articolo | Comma | E
        Numero          := Novella                          | Titolo | Capo | Articolo | Comma | Lettera | E
        Novella         :=                                  | Titolo | Capo | Articolo | Comma | Lettera | Numero | E
    
    
        Rubrica_Titolo  := Capo | Articolo
        Rubrica_Capo    := Articolo
        Rubrica_Art     := Comma
        
        ------------------------------------------------------------------------------------------------------    
    """

    # Creazione DFA mediante sintassi definita in BNF

    S.goto([S_Titolo, S_Capo, S_Art])

    ritorno = [E]
    S_Titolo.goto([S_Titolo_Rubr, S_Capo, S_Art] + ritorno)
    S_Titolo_Rubr.goto([S_Capo, S_Art])

    ritorno += [S_Titolo]
    S_Capo.goto([S_Capo_Rubr, S_Art] + ritorno)
    S_Capo_Rubr.goto(S_Art)

    ritorno += [S_Capo]
    S_Art.goto([S_Art_Rubr, S_Comm] + ritorno)
    S_Art_Rubr.goto(S_Comm)

    ritorno += [S_Art]
    S_Comm.goto([S_Nov, S_Let] + ritorno)

    ritorno += [S_Comm]
    S_Let.goto([S_Nov, S_Num] + ritorno)

    ritorno += [S_Let]
    S_Num.goto([S_Nov] + ritorno)

    ritorno += [S_Num]
    S_Nov.goto(ritorno)

    # Indica il primo stato significativo
    HIGHER_STATE = S_Titolo

    # ################# METODI DI SUPPORTO

    @staticmethod
    def get_automata() -> Stato:
        return GramArticolato.S

    @staticmethod
    def get_higher_state() -> Stato:
        return GramArticolato.HIGHER_STATE

    @staticmethod
    def get_novella() -> Stato:
        return GramArticolato.S_Nov
