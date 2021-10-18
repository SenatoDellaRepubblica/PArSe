import re
import string

from jinja2 import FileSystemLoader, Environment


class PrefazioneParser(object):
    """
    Classe per la gestione del parsing della prefazione di un DDLPRES, DDLMESS, DDLCOMM
    """
    leg: int
    num_ddl: int

    def __init__(self, prefazione: str):

        self.prefazione = prefazione

        # dictionary delle proprietà del DDL per il template
        self.dic_prop = dict()

        # dictionary del frontespizio e relazione del DDLPRES per il template
        self.dic_ddlpres = dict()

        env = Environment(loader=FileSystemLoader('.'))
        self.template = env.get_template('engine/template/static/ddlpres/ddlpres-pre.tpl.xml')

    def parse_prefazione(self):
        """
        Esegue il parsing della prefazione
        :return:
        """

        # eseguo il parsing delle proprietà del DDL
        lastidx = self._parse_ddl_prop()

        # in base alla tipologia richiama il parser opportuno
        ddlpres_test = re.search(r"DISEGNO\s+DI\s+LEGGE.*?(iniziativa|presentato)", self.prefazione,
                                 re.IGNORECASE | re.DOTALL)
        ddlmess_test = False
        ddlcomm_test = False

        if ddlpres_test:
            return self._parse_ddlpres(lastidx)
        elif ddlmess_test:
            return self._parse_ddlmess(lastidx)
        elif ddlcomm_test:
            return self._parse_ddlcomm(lastidx)
        else:
            return f"<dl:Front><div><![CDATA[{self.prefazione}]]></div></dl:Front>"

    def _parse_ddl_prop(self) -> int:
        """
        esegue il parsing delle proprietà del DDL (indipendentemente dal tipo)
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

        m = re.search(r"Senato\s+della\s+Repubblica.+?(?P<leg>[IVXLCDM]+)\s+legislatura", self.prefazione,
                      re.IGNORECASE | re.DOTALL)
        if m:
            self.dic_prop['leg'] = converti_da_num_romano((m.groupdict()["leg"].strip()))
            new_m = re.compile(r"N\.\s+(?P<num_ddl>\d.+)", re.IGNORECASE).search(self.prefazione, m.end())
            if new_m:
                self.dic_prop['num_ddl'] = new_m.groupdict()["num_ddl"].strip()
                return new_m.end()
            return m.end()
        return -1

    def _parse_ddlpres(self, start_pos: int):
        """
        Esegue il parsing di una prefazione di tipo DDLPRES
        :return:
        """

        # TODO: parsing degli elementi del frontespizio per un DDLPRES

        ptrn_comunicato = re.compile(r"(?P<DATA_COM_INCIPIT>COMUNICATO\s+ALLA\s+PRESIDENZA\s+IL\s+(?P<DATA_COM>.*))")
        ptrn_inizi_parlam = re.compile(r"(?P<FIRMS_INCIPIT>d.+?iniziativa\s+de\w\s+senator\w\s+)(?P<FIRMS>.*)")
        ptrn_present_governo = re.compile(r"(?P<RUOLO>(?:Ministro|Presidente).*?)\((?P<NOME>.*?)\)", flags = re.IGNORECASE|re.DOTALL)
        ptrn_titolo = re.compile(r"\w+([\d\w,.\s°:;+']+[-]?)+[^-]")
        ptrn_relazione = re.compile(r"^relazione.+", re.IGNORECASE | re.DOTALL | re.MULTILINE)
        ptrn_relazione2 = re.compile(r"r[ ]{0,2}e[ ]{0,2}l[ ]{0,2}a[ ]{0,2}z[ ]{0,2}i[ ]{0,2}o[ ]{0,2}n[ ]{0,2}e.*", re.IGNORECASE | re.DOTALL | re.MULTILINE)

        presentatori = list()
        pos = start_pos
        # parsing della iniziativa parlamentare

        m = ptrn_inizi_parlam.search(self.prefazione, pos=pos)
        if m:
            # parsing della iniziativa Parlamentare
            presentatori = [{'nome': s.strip(), 'tipo': "Senatore"}  for s in re.split(r"[,e]", m.groupdict()['FIRMS'])]
            self.dic_ddlpres['iniziativa'] = 'Parlamentare'
        else:

            # parsing della data di comunicazione: serve per limitare la ricerca dei presentatori
            m_comunicato = ptrn_comunicato.search(self.prefazione, pos=pos)
            if m_comunicato:
                pos_comunicato = m_comunicato.start()
                # parsing della iniziativa della PdC
                m = ptrn_present_governo.finditer(self.prefazione, pos=pos, endpos=pos_comunicato)
                presentatori = [{'nome': item.groupdict()['NOME'].strip(), 'tipo': item.groupdict()['RUOLO'].strip()} for item in m]
                self.dic_ddlpres['iniziativa'] = 'Governativa'

        if m:
            # TODO: l'incipit per il momento lo hardencodato dentro
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
            self.dic_ddlpres['titolo'] = m.group().strip()
            pos = m.end()

        # parsing della Relazione (per il momento contiene tutte le tipologie di relazioni: tecnica, AIR, generale, etc. )
        m = ptrn_relazione.search(self.prefazione, pos=pos)
        if m:
            self.dic_ddlpres['relazione'] = m.group().strip()
            pos = m.end()
        else:
            m = ptrn_relazione2.search(self.prefazione, pos=pos)
            if m:
                self.dic_ddlpres['relazione'] = m.group().strip()
                pos = m.end()


        # applica gli elementi al template ed esce
        return self.template.render(dic_prop=self.dic_prop, dic_ddlpres=self.dic_ddlpres)

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
