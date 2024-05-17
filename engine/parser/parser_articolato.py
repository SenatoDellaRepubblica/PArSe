import logging
import re
import sys
from typing import Type

from colorama import Fore

import config
from config import SOGLIA_CHIUSURE, SOGLIA_MAX_RICORSIONE, DEBUG, DEBUG_ESTESO, MARKER_INIZIO_ARTICOLATO
from engine.grammars.articolato.gram_art_novella import GramArticolatoInNovella
from engine.grammars.articolato.gram_articolato import GramArticolato
from engine.exceptions import ParserException
from engine.misc.misc import pretty_print_xml
from engine.misc.output import print_out_and_log
from engine.grammars.grams import TK_ATTR, Stato, Transizione, INFINITE
from engine.parser.parser_coda import CodaParser
from engine.parser.parser_prefazione import PrefazioneParser
from engine.template.tpl_mgr import art_in_senxml_tpl

TAGS_REGEX = r'<[^>]+>'
CATTURA_GRP = 'CORPO'

logger = logging.getLogger(__name__)


class ParserArticolato(object):
    """
    Parser dell'articolato
    """

    # TODO: da cancellare
    # _GRN: Type[GramArticolatoInNovella]
    # _GRA: Type[GramArticolato]

    def __init__(self, gram_articolato: Type[GramArticolato], gram_novella: Type[GramArticolatoInNovella],
                 gram_nov_com_non_num: Type[GramArticolatoInNovella]):
        # Contatore delle ricorsioni
        self._count_ricorsione = 0
        # grammatica
        self._GRA = gram_articolato
        self._GRN = gram_novella
        self._GRN_CNN = gram_nov_com_non_num

    def _parse_art_nov_commi_non_numerati(self, parsed_text, flags=re.MULTILINE | re.IGNORECASE | re.DOTALL):
        """
        Esegue il parsing di una novella con commi non numerati

        :param parsed_text:
        :param flags:
        :return:
        """

        tags = re.search(TAGS_REGEX, parsed_text, flags)
        if tags:
            commi_match = re.search(self._GRN.REGEX_COMMA, parsed_text, flags)
            if not commi_match:
                # pulisco l'articolo dai tag e ottengo tutti i commi non numerati

                m = re.search(fr"</{self._GRN.RUBR}>(?P<{CATTURA_GRP}>[^<]+)</{self._GRN.ART}>", parsed_text, flags)
                if m:
                    corpo = m.group(CATTURA_GRP)
                    start = m.start(CATTURA_GRP)  # inizio del corpo catturato
                    end = m.end(CATTURA_GRP)  # fine del corpo catturato

                    # processa i paragrafi e li numera
                    nuovo_corpo = str()
                    cont_comm = 1
                    for p in corpo.splitlines():
                        if len(p.strip()) > 0:
                            # scarta i paragrafi che non sono lettere: a) b) ...
                            if not re.match(fr"^\w\)\s+", p, flags):
                                # aggiunge il numero del comma
                                nuovo_corpo += f'{cont_comm}. {p}\n'
                                cont_comm += 1
                            else:
                                nuovo_corpo += f'{p}\n'

                    parsed_commi_nn = self._parse_articolato(self._GRN_CNN, self._GRN_CNN.get_automata(), nuovo_corpo)

                    # includo i nuovi commi parsati dentro al testo
                    parsed_text = parsed_text[:start] + parsed_commi_nn + parsed_text[end:]

        return parsed_text

    def _parse_articolato_in_novelle(self, txt: str,
                                     flags=re.MULTILINE | re.IGNORECASE | re.DOTALL):
        """
        Parsing del testo all'interno delle novelle

        :param txt:
        :param flags:
        :return:
        """

        gramm = self._GRN

        tipo_stato = gramm.get_novella().tk_type
        items = re.finditer(gramm.REGEX_NOVELLA_XML, txt, flags)
        ret = txt
        delta = 0
        for m in items:

            if DEBUG and DEBUG_ESTESO:
                print_out_and_log(f'===> Parsing Novella: <NOVELLA>{m.group(gramm.CPART)}</NOVELLA>')

            # esegue il parsing della Novella
            out = self._parse_articolato(gramm, gramm.get_automata(), m.group(gramm.CPART))

            # se non ci sono commi numerati allora procede con il parsing del corpo
            out = self._parse_art_nov_commi_non_numerati(out, flags)

            # fa il replace e mette in coda il risultato
            sub = gramm.grm_tk_dic[tipo_stato][TK_ATTR.REPL_S].replace(gramm.REPL_CPART, out)
            ret = ''.join([ret[:m.start(1) + delta], sub, ret[m.end(1) + delta:]])
            delta += len(sub) - (m.end(1) - m.start(1))

        return ret

    def _rollback_tag_novelle(self, txt: str,
                              flags=re.MULTILINE | re.IGNORECASE | re.DOTALL):
        """
        Ripristina i caporali per le novelle senza TAG al proprio interno
        (ovvero le novelle che non contengono partizioni di articolato sono ripristinate con i caporali)

        :param txt:
        :param flags:
        :return:
        """

        items = re.finditer(self._GRA.REGEX_NOVELLA_XML, txt, flags)
        ret = txt
        delta = 0
        for m in items:

            # controlla se all'interno ci sono tag
            body_novella = m.group(self._GRA.CPART)
            m1 = re.search(TAGS_REGEX, body_novella, flags)

            # se non ha trovato TAG all'interno della novella allora ripristina
            if not m1:
                sub = f"«{body_novella}»"

                if DEBUG and DEBUG_ESTESO:
                    print_out_and_log(f'==> Rollback per Novella (senza articolato): <NOVELLA>{body_novella}</NOVELLA>')

                # fa il replace e mette in coda il risultato
                start = m.start(1)
                end = m.end(1)
                ret = ''.join([ret[:start + delta], sub, ret[end + delta:]])
                delta += len(sub) - (end - start)

        return ret

    def main_parse(self, txt: str, mark: str = '',
                   flags=re.MULTILINE | re.IGNORECASE | re.DOTALL, parse_novelle: bool = True) -> str:
        """
        Esegue il parsing partendo da un marcatore nel testo (cerca l'ultima occorrenza del marcatore)

        :param flags: flag per le espressioni regolari
        :param txt: testo da processare
        :param mark: marcatore dopo il quale eseguire il parsing
        :param parse_novelle: se bisogna parsare l'articolato dentro le novelle
        :return:
        """

        def put_alinea_corpo_h_p(xml, flags):
            """
            Inserisce ALINEA e CORPO nell'XML marcato

            :param xml:
            :param flags:
            :return:
            """
            # return xml

            ret = xml
            delta = 0

            matches = re.finditer(
                fr'(?P<PRE><{self._GRA.NS}[^>]*>\s*?<{self._GRA.NUM}\b[^>]*>.*?</{self._GRA.NUM}>(?:\s*<{self._GRA.RUBR}>[^<]*</{self._GRA.RUBR}>)?)' +
                fr'(?P<BODY>[^<]*)' +
                fr'(?P<POST>(?=<{self._GRA.NS}\w+>)|</{self._GRA.NS}\w+>)',
                xml, flags=flags)

            for m in matches:

                # mette gli H:P dentro al corpo di ALINEA e CORPO
                body = m.group('BODY').strip()
                body = re.sub(r'^\s*(.+)', r'<h:p>\g<1></h:p>', body, flags=re.I | re.M)

                if body:
                    # Esiste la chiusura del tag, quindi Wrappo BODY con <a:Corpo>
                    if m.group('POST'):
                        newbody = f'{m.group("PRE")}<{self._GRA.CORPO}>{body}</{self._GRA.CORPO}>{m.group("POST")}'
                    # Non esiste la chiusura del tag, quindi Wrappo BODY con <a:Alinea>
                    else:
                        newbody = f'{m.group("PRE")}<{self._GRA.ALINEA}>{body}</{self._GRA.ALINEA}>{m.group("POST")}'

                    ret = ''.join([ret[:m.start() + delta], newbody, ret[m.end() + delta:]])
                    delta += len(newbody) - (m.end() - m.start())

            return ret

        def bonifica_h_p(xml, flags):
            """
            Sistema gli <H:P> eliminando gli spazi all'inizio e alla fine e gli elementi vuoti

            :param xml:
            :param flags:
            :return:
            """

            ret = xml
            delta = 0
            matches = re.finditer(fr'(?P<PRE><{"h:p"}>)(?P<BODY>[^<]+)(?P<POST></{"h:p"}>)', xml, flags=flags)
            for m in matches:
                body = m.group('BODY').strip()
                # mette il P bonificato strippando gli spazi bianchi
                if body:
                    newbody = f'{m.group("PRE")}{body}{m.group("POST")}'
                # elimina <H:P></H:P> vuoti, senza corpo
                else:
                    newbody = ''

                ret = ''.join([ret[:m.start() + delta], newbody, ret[m.end() + delta:]])
                delta += len(newbody) - (m.end() - m.start())

            return ret

        # Individua il marcatore di inizio dell'articolato: euristika debole...
        if DEBUG:
            print_out_and_log(Fore.YELLOW + f"Parsing della relazione introduttiva" + Fore.RESET)

        prefazione, prefazione_parsed = '', ''
        markers = [i for i in re.finditer(mark, txt, flags=re.MULTILINE | re.IGNORECASE)]
        if markers:
            # prende l'ultimo marcatore individuato
            if DEBUG:
                print_out_and_log(f"Marcatore di inizio dell'articolato trovato: {markers[-1].group()}")
            idx = markers[-1].start()
            # prefazione = f"<![CDATA[{txt[:idx]}]]>"
            prefazione = txt[:idx]
            resto_documento = CodaParser(txt[idx:]).cancella_coda('dl')

            parser_prefazione = PrefazioneParser(prefazione)
            prefazione_parsed = parser_prefazione.parse_prefazione()
            xml = self._parse_articolato(self._GRA, self._GRA.get_automata(), txt_post=resto_documento)
        else:
            # esegue il solo parsing dell'articolato
            if DEBUG:
                print_out_and_log("Marcatore di inizio dell'articolato non trovato!")
            xml = self._parse_articolato(self._GRA, self._GRA.get_automata(),
                                         txt_post=CodaParser(txt).cancella_coda('ddl'))

        # esegue il flush della diagnostica
        sys.stderr.flush()

        # effettua il parsing all'interno delle novelle
        if parse_novelle:
            if DEBUG:
                print_out_and_log(Fore.YELLOW + "Paring delle novelle" + Fore.RESET)
            xml = self._parse_novelle(xml, flags=flags)

        # mette ALINEA e CORPO
        xml = put_alinea_corpo_h_p(xml, flags=flags)

        # separa l'articolato vero e proprio dall'incipit del DDL o del Decreto-Legge
        idx = xml.index("<") if "<" in xml else 0
        if mark == MARKER_INIZIO_ARTICOLATO["decretoLegge"]:
            incipit_art = "DECRETO-LEGGE"
            xml_art = xml[idx:]
            xml = art_in_senxml_tpl("dl", incipit_art, xml_art, prefazione_parsed)
        else:
            incipit_art = xml[:idx].strip()
            xml_art = xml[idx:]
            xml = art_in_senxml_tpl("ddl", incipit_art, xml_art, prefazione_parsed)

        # formatta l'XML con un Pretty Print: attenzione inserisce new line
        xml = pretty_print_xml(xml)

        # sistema gli H:P eliminando gli spazi bianchi iniziali e finali dovuti al pretty print
        xml = bonifica_h_p(xml, flags=flags)

        return xml

    def _parse_novelle(self, xml: str, flags) -> str:
        """
        Elabora le novelle dentro l'articolato
        :param xml:
        :return:
        """
        # testare bene
        m = re.search(r'<[^>]+?>.*</[^>]+?>', xml, flags)
        if m:
            body = self._parse_articolato_in_novelle(m.group())
            new_body = self._rollback_tag_novelle(body)
            xml = xml[:m.start()] + new_body + xml[m.end():]

        return xml

    def _parse_articolato(self, gramm: Type[GramArticolato], curr_state: Stato, txt_post: str, txt_pre: str = '',
                          stack_stati_chiusura: list = None) -> str:
        """
        Automa interno che procede sugli stati definiti nella grammatica

        È l'algoritmo principale di visita sul DFA definito.

        Si mangiano caratteri e si decide in che stato andare a seconda della grammatica definita.

        :param gramm Grammatica da utilizzare (specializzate di self.GA)
        :param stack_stati_chiusura: stack degli stati processari
        :param curr_state: stato corrente
        :param txt_pre: testo PREcente già processato
        :param txt_post: testo POST da processare
        :return:
        """

        self._count_ricorsione += 1

        # https: // docs.python - guide.org / writing / gotchas /
        if stack_stati_chiusura is None:
            stack_stati_chiusura = list()

        def get_chiusura_stato(stato_end: Stato) -> str:
            """
            Calcola la lista di token da chiudere quando si transita da uno stato con posizione più grande
            rispetto a uno con posizione più piccola (si risale l'albero)

            :param stato_end: stato di arrivo
            :return:
            """

            closure = ''
            if len(stack_stati_chiusura) > 0:
                stato_start = stack_stati_chiusura[-1]
                start = gramm.grm_tk_dic[stato_start.tk_type]
                end = gramm.grm_tk_dic[stato_end.tk_type]
                if end[TK_ATTR.POS] <= start[TK_ATTR.POS]:

                    if DEBUG and DEBUG_ESTESO:
                        print_out_and_log(
                            f'[Closure] Start token: {Fore.MAGENTA}{str(stato_start)} --> End token: {str(stato_end)}{Fore.RESET}')
                        print_out_and_log(f'[Closure] Tokens stack: {Fore.MAGENTA}{stack_stati_chiusura}{Fore.RESET}')

                    cont = 0
                    # Comincio a ciclare per tutto lo stack fino a che non raggiungo lo stato di fine
                    while True:

                        if start[TK_ATTR.REPL_C] and end[TK_ATTR.POS] <= start[TK_ATTR.POS]:
                            try:
                                stato_start = stack_stati_chiusura.pop()
                                start = gramm.grm_tk_dic[stato_start.tk_type]
                            except IndexError:
                                stato_start = None

                            # crea la stringa della chiusura
                            # cambiata!
                            closure += start[TK_ATTR.REPL_C]
                            # closure = ''.join((closure, start[TK_ATTR.REPL_C]))
                            if DEBUG and DEBUG_ESTESO:
                                print_out_and_log(f'[Closure] Final value: {Fore.MAGENTA}{closure.strip()}{Fore.RESET}')

                        if stato_start is None or \
                                not stack_stati_chiusura or \
                                stato_start is stato_end:
                            break

                        """
                        Messaggio di debug per superamento della soglia di sicurezza
                        
                        Questo messaggio viene visualizzato quando si cerca di chiudere i tag con una gerarchia che non è quella corretta. Quindi
                        da un token gerarchicamente più in alto verso uno più in basso, invece che da un token più in basso verso uno più in alto.
                        Ad esempio, se dopo il comma si risale ad una lettera, questo non è
                        corretto perché dal comma si risale verso l'articolo e non la lettera
                        """

                        cont += 1
                        if cont >= SOGLIA_CHIUSURE:
                            print_out_and_log(
                                f'[Closure]{Fore.RED}[Errore]{Fore.RESET} Lo stato iniziale transita in uno stato finale non superiore gerarchicamente! Da {str(stato_start)} si sta risalendo a {str(stato_end)}')

                            # TODO: invece dell'eccezione si ritorna comunque la chiusura trovata, anche se scorretta; inviare in qualche modo un errore
                            # raise ParserException(f"=====> {Fore.RED}Soglia massima raggiunta per le chiusure!!!{Fore.RESET}")
                            config.context_messages['warnings'].append("Soglia massima raggiunta per le chiusure!!!")
                            break

            return closure

        def match_next_stato(state_to_match: Stato, t_pre: str, t_post: str, trans_list: list) -> list:
            """
            Esegue il match sul testo della regex associata allo Stato
            :param state_to_match: stato corrente
            :param t_pre: testo processato
            :param t_post: testo da processare
            :param trans_list: lista delle transizioni da popolare
            :return: la coppia aggiornata dei valori txt_processed, text_todo
            """

            current_tk = gramm.grm_tk_dic[state_to_match.tk_type]
            # cerca il prossimo token dalla grammatica
            match = re.search(current_tk[TK_ATTR.REGEX], t_post, gramm.FLAGS)
            if match:
                # compone la parte da sostituire
                sub = current_tk[TK_ATTR.REPL_S].replace(gramm.REPL_CPART, match.group(gramm.CPART)).replace(
                    gramm.REPL_SPART, match.group(gramm.SPART))
                pre = t_post[:match.start(gramm.SPART)]

                t_post = t_post[match.end(gramm.SPART):]
                t_pre = ''.join([t_pre, pre])

                trans = Transizione(state_to_match, t_post, sub, '', t_pre)
                trans_list.append(trans)
            else:
                if DEBUG and DEBUG_ESTESO:
                    print_out_and_log(f"(no match: {str(state_to_match.tk_type)})")

            return trans_list

        def calc_next_trans(tr_list: list) -> Transizione:
            """
            Determina qual è lo stato più prossimo dalla posizione corrente
            :param tr_list: lista delle transizioni possibili
            :return:
            """

            chosen_t, min_txt = None, None
            for t in tr_list:
                if min_txt is None or len(t.txt_pre) < min_txt:
                    chosen_t, min_txt = t, len(t.txt_pre)
            return chosen_t

        # XXX: ================== PROCEDURA PRINCIPALE ==============================

        if DEBUG and curr_state == gramm.get_automata():
            print_out_and_log(Fore.YELLOW + f"Parsing dell\'Articolato (gramm: {gramm})" + Fore.RESET)

        # Se non sono all'inizio o alla fine allora processo le transizioni
        if curr_state is not gramm.E:

            # inizializza le liste di supporto
            trans_list = []

            """
            Se sono arrivato in questo stato devo controllare se la molteplicità
            dello stato definita nella grammatica è multipla (ovvero >1). In questo caso
            allora devo fare il check con lo stesso stato in cui sono per inserirlo nelle possibili
            transizioni
            
            Popolo la lista delle possibili transizioni
            """
            # if curr_state is not S and curr_state.mul == INFINITE:
            if curr_state.mul == INFINITE:
                tot = txt_pre + txt_post
                trans_list = match_next_stato(curr_state, tot[:len(txt_pre) + 1], tot[len(txt_pre) + 1:], trans_list)

            """
            Match degli stati destinazione delle transizioni: solo se ci sono transizioni
            
            Popolo la lista delle possibili transizioni (partendo dalla precedente)
            """
            if len(curr_state.trans) > 0:
                # determina la lista delle possibili transizioni eseguendo il match
                for stato_dst in curr_state.trans:
                    # TODO: ma perché questo test? Il tipo di token esiste sempre...
                    if stato_dst.tk_type:
                        trans_list = match_next_stato(stato_dst, txt_pre, txt_post, trans_list)

            # ritorna la transizione più conveniente, ovvero quella che ha un match più vicino
            next_trans = calc_next_trans(trans_list)

            # ATTENZIONE: va lasciata la riga seguente, altrimenti c'è occupazione di memoria mostruosa nella ricorsione
            trans_list = []

            # esegue il passo ricorsivo sulla transizione scelta
            if (next_trans is not None and
                    (self._count_ricorsione < SOGLIA_MAX_RICORSIONE or SOGLIA_MAX_RICORSIONE == 0)):
                if DEBUG:
                    print_out_and_log(f'==> Next token matched: {Fore.MAGENTA}{str(next_trans)}{Fore.RESET}')

                # determina la chiusura della transizione
                next_trans.chiusura = get_chiusura_stato(next_trans.stato_dst)

                """
                Appende lo stato di destinazione allo stack degli stati:
                solo se lo stato di destinazione ha un REPL_C non vuoto
                """
                next_stato = gramm.grm_tk_dic[next_trans.stato_dst.tk_type]
                if next_stato[TK_ATTR.REPL_C]:
                    stack_stati_chiusura.append(next_trans.stato_dst)

                # aggiorna il txt_pre con la chiusura seguita dalla sostituzione del token trovato
                new_txt_pre = ''.join([next_trans.txt_pre, next_trans.chiusura, next_trans.rep])

                return self._parse_articolato(gramm, next_trans.stato_dst, next_trans.txt_post, new_txt_pre,
                                              stack_stati_chiusura)

        if DEBUG and DEBUG_ESTESO:
            print_out_and_log('[Closure] Final document closure applied')
        chiusura = get_chiusura_stato(gramm.get_higher_state())

        # esco dalla ricorsione restituendo il testo marcato
        if DEBUG:
            print_out_and_log("[End]: Recursion end")
        return ''.join([txt_pre, txt_post, chiusura])
