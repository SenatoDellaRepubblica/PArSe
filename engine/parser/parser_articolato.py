
import logging
import re
import sys
from typing import Type

from config import SOGLIA_CHIUSURE, SOGLIA_MAX_RICORSIONE, DEBUG, DEBUG_ESTESO
from engine.grammars.articolato.gram_art_novella import GramArticolatoInNovella
from engine.grammars.articolato.gram_articolato import GramArticolato
from engine.exceptions import ParserException
from engine.misc.misc import pretty_print_xml
from engine.misc.output import print_out_and_log
from engine.grammars.grams import TK_ATTR, Stato, Transizione, INFINITE
from engine.parser.parser_prefazione import PrefazioneParser
from engine.template.tpl_mgr import art_in_senxml_tpl

logger = logging.getLogger(__name__)


class ParserArticolato(object):
    """
    Parser dell'articolato
    """
    _GRN: Type[GramArticolatoInNovella]
    _GRA: Type[GramArticolato]

    def __init__(self, gram_articolato: Type[GramArticolato], gram_novella: Type[GramArticolatoInNovella]):
        # Contatore delle ricorsioni
        self._count_ricorsione = 0
        # grammatica
        self._GRA = gram_articolato
        self._GRN = gram_novella

    def _parse_articolato_in_novelle(self, txt: str, flags=re.MULTILINE | re.IGNORECASE | re.DOTALL):
        """
        Parsing del testo all'interno delle novelle

        :param txt:
        :param flags:
        :return:
        """
        tipo_stato = self._GRN.get_novella().tk_type
        items = re.finditer(self._GRN.REGEX_NOVELLA_XML, txt, flags)
        ret = txt
        delta = 0
        for m in items:

            if DEBUG and DEBUG_ESTESO:
                print_out_and_log('*' * 10)
                print_out_and_log(f'===> Parsing Novella: <NOVELLA>{m.group(self._GRN.CPART)}</NOVELLA>')

            # esegue il parsing all'interno della novella
            gr_orig = self._GRA
            self._GRA = self._GRN
            out = self._parse_articolato(self._GRA.get_automata(), m.group(self._GRN.CPART))
            self._GRA = gr_orig

            # fa il replace e mette in coda il risultato
            sub = self._GRN.grm_tk_dic[tipo_stato][TK_ATTR.REPL_S].replace(self._GRN.REPL_CPART, out)
            ret = ''.join([ret[:m.start(1) + delta], sub, ret[m.end(1) + delta:]])
            delta += len(sub) - (m.end(1) - m.start(1))
            if DEBUG and DEBUG_ESTESO:
                print_out_and_log('*' * 10)

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

        def wrap_con_caporali(body_nov):
            """
            Wrappa la novella con i caporali: se il numero di caporali è dispari aggiunge quello alla fine,
            altrimenti significa che c'è già

            :param body_nov:
            :return:
            """

            return '«' + body_nov

        items = re.finditer(self._GRA.REGEX_NOVELLA_XML, txt, flags)
        ret = txt
        delta = 0
        for m in items:

            # controlla se all'interno ci sono tag
            body_novella = m.group(self._GRA.CPART)
            m1 = re.search(r'<[^>]+>', body_novella, flags)
            if not m1:
                sub = wrap_con_caporali(body_novella)

                if DEBUG and DEBUG_ESTESO:
                    print_out_and_log(f'==> Rollback per Novella (senza articolato): <NOVELLA>{body_novella}</NOVELLA>')

                # fa il replace e mette in coda il risultato
                start = m.start(1)
                end = m.end(1)
                ret = ''.join([ret[:start + delta], sub, ret[end + delta:]])
                delta += len(sub) - (end - start)

        return ret

    def execute(self, txt: str, mark: str = '',
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
            pattern = fr'(?P<PRE><{self._GRA.NS}\w+>\s*?<{self._GRA.NUM}[^/]*/>)(?P<BODY>[^<]*)(?P<POST>(?=<{self._GRA.NS}\w+>)|</{self._GRA.NS}\w+>)'

            ret = xml
            delta = 0
            matches = re.finditer(pattern, xml, flags=flags)
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

        def insert_caporale_iniz_novella(xml: str,
                                         flags=re.MULTILINE | re.IGNORECASE | re.DOTALL):
            """
            Inserisce il caporale iniziale nel primo H:P della novella

            :param xml:
            :param flags:
            :return:
            """

            novelle = re.finditer(self._GRA.REGEX_NOVELLA_XML, xml, flags)
            ret = xml
            delta = 0
            for m in novelle:
                body_novella = m.group(self._GRA.CPART)
                sub = re.sub(r'(.*?<h:p>)', r'\g<0>«', body_novella, count=1, flags=re.MULTILINE | re.IGNORECASE)
                sub = fr'<{self._GRA.TOKEN_NOVELLA}>{sub}</{self._GRA.TOKEN_NOVELLA}>'

                # fa il replace e mette in coda il risultato
                start, end = m.start(1), m.end(1)
                ret = ''.join([ret[:start + delta], sub, ret[end + delta:]])
                delta += len(sub) - (end - start)

            return ret

        # Individua il marcatore di inizio dell'articolato: euristika debole...

        prefazione, prefazione_parsed = '', ''
        markers = [i for i in re.finditer(mark, txt, flags=re.MULTILINE | re.IGNORECASE)]
        if markers:
            # prende l'ultimo marcatore individuato
            print_out_and_log(f"Marcatore di inizio dell'articolato trovato: {markers[-1].group()}")
            idx = markers[-1].start()
            # prefazione = f"<![CDATA[{txt[:idx]}]]>"
            prefazione = txt[:idx]

            # TODO: inserire il parse della prefazione: primo DDLPRES
            parser_prefazione = PrefazioneParser(prefazione)
            prefazione_parsed = parser_prefazione.parse_prefazione()
            xml = self._parse_articolato(self._GRA.get_automata(), txt_post=txt[idx:])
        else:
            # esegue il solo parsing dell'articolato
            print_out_and_log("Marcatore di inizio dell'articolato non trovato!")
            xml = self._parse_articolato(self._GRA.get_automata(), txt_post=txt)

        # esegue il flush della diagnostica
        sys.stderr.flush()

        # effettua il parsing all'interno delle novelle
        if parse_novelle:
            xml = self._elabora_novelle(xml, flags=flags)

        # mette ALINEA e CORPO
        xml = put_alinea_corpo_h_p(xml, flags=flags)

        # separa l'articolato vero e proprio dall'incipit del DDL
        idx = xml.index("<") if "<" in xml else 0
        incipit_art, xml_art = xml[:idx], xml[idx:]

        # mette l'articolato nel template complessivo
        # xml = art_in_senxml_tpl(incipit_art, xml_art, prefazione)
        xml = art_in_senxml_tpl(incipit_art, xml_art, prefazione_parsed)

        # formatta l'XML con un Pretty Print: attenzione inserisce new line
        xml = pretty_print_xml(xml)

        # sistema gli H:P eliminando gli spazi bianchi iniziali e finali dovuti al pretty print
        xml = bonifica_h_p(xml, flags=flags)

        # sistema i caporali iniziali della novella marcata: va dopo il pretty print
        if parse_novelle:
            xml = insert_caporale_iniz_novella(xml, flags=flags)

        return xml

    def _elabora_novelle(self, xml: str, flags) -> str:
        """
        Elabora le novelle dentro l'articolato
        :param xml:
        :return:
        """
        # testare bene
        m = re.search(r'<[^>]+?>.*</[^>]+?>', xml, flags)
        if m:
            body = m.group()
            body = self._parse_articolato_in_novelle(body)
            body = self._rollback_tag_novelle(body)
            xml = xml[:m.start()] + body + xml[m.end():]

        return xml

    def _parse_articolato(self, curr_state: Stato, txt_post: str, txt_pre: str = '',
                          stack_stati_chiusura: list = None) -> str:
        """
        Automa interno che procede sugli stati definiti nella grammatica

        :param stack_stati_chiusura: stack degli stati processari
        :param curr_state: stato corrente
        :param txt_pre: testo processato
        :param txt_post: testo da processare
        :return:
        """

        self._count_ricorsione += 1

        # https: // docs.python - guide.org / writing / gotchas /
        if stack_stati_chiusura is None:
            stack_stati_chiusura = list()

        def get_chiusura_stato(stato_end: Stato) -> str:
            """
            Calcola la lista di token da chiudere quando si transita
            da uno stato con posizione più grande rispetto ad uno con posizione più piccola (si risale l'albero)
            :stato_start: stato di provenienza
            :stato_end: stato di arrivo
            :return:
            """

            closure = ''
            if len(stack_stati_chiusura) > 0:
                stato_start = stack_stati_chiusura[-1]
                start = self._GRA.grm_tk_dic[stato_start.tk_type]
                end = self._GRA.grm_tk_dic[stato_end.tk_type]
                if end[TK_ATTR.POS] <= start[TK_ATTR.POS]:

                    if DEBUG and DEBUG_ESTESO:
                        print_out_and_log(
                            f'[Closure] Start token: {str(stato_start)} --> End token: {str(stato_end)}')
                        print_out_and_log(f'[Closure] Tokens stack: {stack_stati_chiusura}')

                    cont = 0
                    # Comincio a ciclare per tutto lo stack fino a che non raggiungo lo stato di fine
                    while True:

                        if start[TK_ATTR.REPL_C] and end[TK_ATTR.POS] <= start[TK_ATTR.POS]:
                            try:
                                stato_start = stack_stati_chiusura.pop()
                                start = self._GRA.grm_tk_dic[stato_start.tk_type]
                            except IndexError:
                                stato_start = None

                            # crea la stringa della chiusura
                            # cambiata!
                            closure += start[TK_ATTR.REPL_C]
                            # closure = ''.join((closure, start[TK_ATTR.REPL_C]))
                            if DEBUG and DEBUG_ESTESO:
                                print_out_and_log(f'[Closure] Final value: "{closure.strip()}"')

                        if stato_start is None or \
                                not stack_stati_chiusura or \
                                stato_start is stato_end:
                            break

                        # messaggio di debug per superamento della soglia di sicurezza
                        cont += 1
                        if cont >= SOGLIA_CHIUSURE:
                            print_out_and_log(
                                f'[Closure] loop per Start: {str(stato_start)} --> End: {str(stato_end)}')
                            raise ParserException("=====> Maximum threshold reached for the closure")

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

            current_tk = self._GRA.grm_tk_dic[state_to_match.tk_type]
            # cerca il prossimo token dalla grammatica
            match = re.search(current_tk[TK_ATTR.REGEX], t_post, self._GRA.FLAGS)
            if match:
                # compone la parte da sostituire
                sub = current_tk[TK_ATTR.REPL_S].replace(self._GRA.REPL_CPART, match.group(self._GRA.CPART))
                pre = t_post[:match.start(self._GRA.SPART)]

                t_post = t_post[match.end(self._GRA.SPART):]
                t_pre = ''.join([t_pre, pre])

                trans = Transizione(state_to_match, t_post, sub, '', t_pre)
                trans_list.append(trans)
            else:
                if DEBUG and DEBUG_ESTESO:
                    print_out_and_log(f"(no match: {str(state_to_match.tk_type)})")

            return trans_list

        def calc_next_trans(tr_list: list) -> Transizione:
            """
            Determina qual'è lo stato più prossimo dalla posizione corrente
            :param tr_list: lista delle transizioni possibili
            :return:
            """

            chosen_t, min_txt = None, None
            for t in tr_list:
                if min_txt is None or len(t.txt_pre) < min_txt:
                    chosen_t, min_txt = t, len(t.txt_pre)
            return chosen_t

        # inizializza le liste di supporto
        trans_list = []

        # Se non sono all'inizio o alla fine allora processo le transizioni
        if curr_state is not self._GRA.E:

            """
            Se sono arrivato in questo stato devo controllare se la molteplicità
            dello stato definita nella grammatica è multipla (ovvero >1). In questo caso
            allora devo fare il check con lo stesso stato in cui sono per inserirlo nelle possibili
            transazioni
            """
            # if curr_state is not S and curr_state.mul == INFINITE:
            if curr_state.mul == INFINITE:
                tot = txt_pre + txt_post
                trans_list = match_next_stato(curr_state, tot[:len(txt_pre) + 1], tot[len(txt_pre) + 1:], trans_list)

            """
            Match degli stati destinazione delle transizioni: solo se ci sono transizioni
            """
            if len(curr_state.trans) > 0:
                # determina la lista delle possibili transizioni eseguendo il match
                for stato_dst in curr_state.trans:
                    if stato_dst.tk_type:
                        trans_list = match_next_stato(stato_dst, txt_pre, txt_post, trans_list)

            # ritorna la transizione più conveniente, ovvero quella che ha un match più vicino
            next_trans = calc_next_trans(trans_list)

            # esegue il passo ricorsivo sulla transizione scelta
            if next_trans is not None and (
                    self._count_ricorsione < SOGLIA_MAX_RICORSIONE or SOGLIA_MAX_RICORSIONE == 0):
                if DEBUG:
                    print_out_and_log(f'==> Next token matched: "{str(next_trans)}"')

                # determina la chiusura della transazione
                next_trans.chiusura = get_chiusura_stato(next_trans.stato_dst)

                """
                Appende lo stato di destinazione allo stack degli stati:
                solo se lo stato di destinazione ha un REPL_C non vuoto
                """
                next_stato = self._GRA.grm_tk_dic[next_trans.stato_dst.tk_type]
                if next_stato[TK_ATTR.REPL_C]:
                    stack_stati_chiusura.append(next_trans.stato_dst)

                # aggiorna il txt_pre con la chiusura seguita dalla sostituzione del token trovato
                new_txt_pre = ''.join([next_trans.txt_pre, next_trans.chiusura, next_trans.rep])

                return self._parse_articolato(next_trans.stato_dst, next_trans.txt_post, new_txt_pre,
                                              stack_stati_chiusura)

        if DEBUG and DEBUG_ESTESO:
            print_out_and_log('[Closure] Final dccument closure applied')
        chiusura = get_chiusura_stato(self._GRA.get_higher_state())

        # esco dalla ricorsione restituendo il testo marcato
        if DEBUG:
            print_out_and_log("[End]: Recursion end")
        return ''.join([txt_pre, txt_post, chiusura])
