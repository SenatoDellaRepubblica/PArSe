import logging
from copy import deepcopy

from engine.grammars.articolato.gram_art_novella import GramArticolatoInNovella as GAN
from engine.grammars.grams import Stato, TK_EN, TK_ATTR, StatoStart

logger = logging.getLogger(__name__)


class GramCommiNonNumerati(GAN):
    """
    La grammatica di un Articolato (dentro la Novella) con i SOLI commi non numerati

    Eredita da GramArticolatoInNovella perché ci interessano le partizioni da comma incluso in giù e non quelle superiori
    e la grammatica della novella per queste partizioni è invariante rispetto alla grammatica dell'articolato.
    """

    grm_tk_dic = deepcopy(GAN.grm_tk_dic)

    # inserisco nel comma un attributo per far capire che era un comma non numerato ed è possibile gestirlo diversamente
    grm_tk_dic[TK_EN.COMM][TK_ATTR.REPL_S] = f'<a:Comma>\n<a:Num numero="{GAN.REPL_CPART}" invisibile="1">{GAN.REPL_SPART}</a:Num>'

    # Definizione del DFA
    S = StatoStart()  # deve essere inzializzato qui

    S.goto([GAN.S_Comm, GAN.S_Let])

    @staticmethod
    def get_automata() -> Stato:
        return GramCommiNonNumerati.S
