import re
import string

from jinja2 import FileSystemLoader, Environment

from config import MARKER_INIZIO_ARTICOLATO


class PrefazioneParser(object):
    """
    Classe per la gestione del parsing della prefazione di un DDLPRES, DDLMESS, DDLCOMM
    """
    leg: int
    num_ddl: int

    def __init__(self, prefazione: str):

        env = Environment(loader=FileSystemLoader('.'))

        self.prefazione = prefazione

        # dictionary delle proprietà del DDL per il template
        self.dic_prop = dict()

        # dictionary del frontespizio e relazione del DDLPRES per il template
        self.dic_ddlpres = dict()

        # dictionary del frontespizio e relazione dei DL per il template
        self.dic_dl = dict()

        self.template_ddlpres = env.get_template('engine/template/static/ddlpres/prefazione.incl.tpl.xml')
        self.template_dl = env.get_template('engine/template/static/dl/prefazione.incl.tpl.xml')

    def parse_prefazione(self):
        """
        Esegue il parsing della prefazione
        :return:
        """

        # in base alla tipologia richiama il parser opportuno
        ddlpres_test = re.search(r"DISEGNO\s+DI\s+LEGGE.*?(iniziativa|presentato)|"
                                 r"PROPOSTA\s+DI\s+LEGGE", self.prefazione, re.IGNORECASE | re.DOTALL)

        dl_test = re.search(r"decreto-legge", self.prefazione, re.IGNORECASE | re.DOTALL)

        # TODO: resta da implementare il parsing dei messaggi e delle relazioni
        # ddlmess_test = re.search(r"attesto +che +il +Senato +della +Repubblica.*?ha +approvato", self.prefazione,
        #                         re.IGNORECASE | re.DOTALL)

        ddlmess_test = False
        ddlcomm_test = False

        if ddlpres_test:
            # eseguo il parsing delle proprietà del DDL
            lastidx = self._parse_ddl_prop()
            return self._parse_ddlpres(lastidx)
        elif ddlmess_test:
            # return self._parse_ddlmess(lastidx)
            pass
        elif ddlcomm_test:
            # return self._parse_ddlcomm(lastidx)
            pass
        elif dl_test:
            lastidx = self._parse_dl_prop()
            return self._parse_dl(lastidx)
        else:
            return f"<dl:Front><div><![CDATA[{self.prefazione}]]></div></dl:Front>"

    def _parse_ddl_prop(self) -> int:
        """
        Esegue il parsing delle proprietà del DDL (indipendentemente dal tipo)
        :return:
        """

        def converti_da_num_romano(num_ddl: str) -> int:
            """
            Converte un numero romano in un intero
            :param num_ddl:
            :return:
            """
            rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
            int_val = 0
            for i in range(len(num_ddl)):
                if i > 0 and rom_val[num_ddl[i]] > rom_val[num_ddl[i - 1]]:
                    int_val += rom_val[num_ddl[i]] - 2 * rom_val[num_ddl[i - 1]]
                else:
                    int_val += rom_val[num_ddl[i]]
            return int_val

        m = re.search(
            r"Senato\s+della\s+Repubblica.+?(?P<leg>[IVXLCDM]+)\s+legislatura\s*[_-]*\s*(N\.\s+(?P<num_ddl>\d+))?",
            self.prefazione,
            re.IGNORECASE | re.DOTALL)
        if m:
            self.dic_prop['leg'] = converti_da_num_romano((m.groupdict()["leg"].strip()))
            self.dic_prop['num_ddl'] = m.groupdict()["num_ddl"].strip() if m.groupdict()["num_ddl"] else None
            return m.end()

        return 0

    def _parse_ddlpres(self, start_pos: int):
        """
        Esegue il parsing di una prefazione di tipo DDLPRES
        :return:
        """

        # parsing degli elementi del frontespizio per un DDLPRES

        ptrn_comunicato = re.compile(r"(?P<DATA_COM_INCIPIT>COMUNICATO\s+ALLA\s+PRESIDENZA\s+IL\s+(?P<DATA_COM>.*))")
        ptrn_inizi_parlam = re.compile(r"(?P<FIRMS_INCIPIT>d.+?iniziativa\s+de\w+\s+senat\w+\s+)(?P<FIRMS>.*)")
        ptrn_present_governo = re.compile(r"(?P<RUOLO>(?:Ministro|Presidente).*?)\((?P<NOME>.*?)\)",
                                          flags=re.IGNORECASE | re.DOTALL)
        ptrn_titolo = re.compile(r"[-_]{3,}\s(?P<titolo>.+)\s[-_]{3,}")
        ptrn_relazione = re.compile(r"(^\s*relazione(?:\s*illustrativa\s*)?(?P<relazione1>.+))|"
                                    r"(?P<relazione2>\s*onorevoli[ ]{1,3}(senatori|colleghi)\s*.+)|"
                                    r"(r[ ]{1,2}e[ ]{1,2}l[ ]{1,2}a[ ]{1,2}z[ ]{1,2}i[ ]{1,2}o[ ]{1,2}n[ ]{1,2}e(?P<relazione3>.+))",
                                    re.IGNORECASE | re.DOTALL | re.MULTILINE)

        presentatori = list()
        pos = start_pos

        # parsing della iniziativa parlamentare
        m = ptrn_inizi_parlam.search(self.prefazione, pos=pos)
        if m:
            # parsing della iniziativa Parlamentare
            presentatori = [{'nome': s.strip(), 'tipo': "Senatore"} for s in re.split(r"[,e]", m.groupdict()['FIRMS'])]
            self.dic_ddlpres['iniziativa'] = 'Parlamentare'
        else:
            # parsing della data di comunicazione: serve per limitare la ricerca dei presentatori
            m_comunicato = ptrn_comunicato.search(self.prefazione, pos=pos)
            if m_comunicato:
                pos_comunicato = m_comunicato.start()

                # parsing della iniziativa della PdC
                m = ptrn_present_governo.finditer(self.prefazione, pos=pos, endpos=pos_comunicato)
                presentatori = [{'nome': item.groupdict()['NOME'].strip(), 'tipo': item.groupdict()['RUOLO'].strip()}
                                for item in m]
                self.dic_ddlpres['iniziativa'] = 'Governativa'

        if m:
            # l'incipit per il momento lo hardencodato dentro
            self.dic_ddlpres['iniziativa_incipt'] = "presentato dal"
            self.dic_ddlpres['lista_presentatori'] = presentatori

        m_comunicato = ptrn_comunicato.search(self.prefazione, pos=pos)
        if m_comunicato:
            self.dic_ddlpres['incipit_data_trasmissione_espl'] = m_comunicato.groupdict()['DATA_COM_INCIPIT'].strip()
            self.dic_ddlpres['data_trasmissione_impl'] = m_comunicato.groupdict()['DATA_COM'].strip()
            pos = m_comunicato.end()

        # parsing del titolo del frontespizio
        m = ptrn_titolo.search(self.prefazione, pos=pos)
        if m:
            self.dic_ddlpres['titolo'] = m.group('titolo').strip()
            pos = m.end()

        # parsing della Relazione (per il momento contiene tutte le tipologie di relazioni: tecnica, AIR, generale, etc. )
        m = ptrn_relazione.search(self.prefazione, pos=pos)
        if m:
            self.dic_ddlpres['relazione'] = \
                m.group('relazione1').strip() if m.group('relazione1') \
                    else m.group('relazione2').strip() if m.group('relazione2') \
                    else m.group('relazione3').strip() if m.group('relazione3') \
                    else None

        # applica gli elementi al template ed esce
        return self.template_ddlpres.render(dic_prop=self.dic_prop, dic_ddlpres=self.dic_ddlpres)

    def _parse_dl_prop(self):
        # TODO: impostare le proprietà del DL
        self.dic_prop['num_dl'] = "0"
        self.dic_prop['data'] = "0"
        return 0

    def _parse_dl(self, lastidx):
        # TODO: per il momento prendo tutta la prefazione
        self.dic_dl['num_dl'] = "0"
        self.dic_dl['titolo'] = "N/A"
        self.dic_dl['relazione'] = self.prefazione
        return self.template_dl.render(dic_prop=self.dic_prop, dic_dl=self.dic_dl)

    def _parse_ddlmess(self, start_pos: int):
        """
        Esegue il parsing di una prefazione di tipo DDLMESS
        :return:
        """
        pass

    def _parse_ddlcomm(self, start_pos: int):
        """
        Esegue il parsing di una prefazione di tipo DDLCOMM
        :return:
        """
        pass
