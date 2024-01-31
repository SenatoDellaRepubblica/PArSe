import hashlib
import re
from difflib import context_diff, HtmlDiff
from unittest import TestCase

import config
from engine.misc.misc import del_and_make_dir
from engine.misc.output import print_out
from engine.unittest.unittest_utils import get_parsed_docs


class DocumentEquality(TestCase):
    """
    Classe di test per controllare che i documenti XML e di testo siano uguali
    """

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.path_in = config.UNITTEST_PATH_IN
        cls.path_out = config.UNITTEST_PATH_OUT
        cls.path_diff = config.UNITTEST_PATH_DIFF

    def make_write_diff_file(self, ddl_text, nome_file, orig_xml, parsed_xml, path_diff, risultato):
        suffix = 'OK' if risultato else 'ko'
        diff_name = f'{path_diff}/{suffix}/{nome_file}{".diff." + suffix}'

        # elimina gli "acapo" multipli per un migliore Diff
        pattern = r'(\s*[\n\r]+\s*)+'
        orig_xml = re.sub(pattern, r'\n', orig_xml, flags=re.M | re.DOTALL)
        parsed_xml = re.sub(pattern, r'\n', parsed_xml, flags=re.M | re.DOTALL)

        self.make_diff_files(diff_name, orig_xml, parsed_xml, ddl_text)

    def make_diff_files(self, diff_name, orig_xml, parsed_xml, orig_text):
        """
        Crea i file delle differenze: sia versione TXT che versione HTML

        :param diff_name:
        :param orig_xml:    xml originale
        :param parsed_xml:  xml generato
        :param orig_text:   testo parsato
        :return:
        """

        # scrive il file di testo originale non parsato
        with open(diff_name + '.orig.txt', mode='w', encoding='utf-8') as file:
            file.write(orig_text)

        if parsed_xml != orig_xml:
            parsed_text_splitlines = parsed_xml.splitlines(keepends=True)
            orig_text_splitlines = orig_xml.splitlines(keepends=True)

            # scrive il file di testo con le differenze
            result = list(context_diff(parsed_text_splitlines, orig_text_splitlines))
            with open(diff_name + '.txt', mode='w', encoding='utf-8') as file:
                file.writelines(result)

            # scrive un file html con la comparazione side by side
            d = HtmlDiff(tabsize=4, wrapcolumn=60)
            result = list(d.make_file(orig_text_splitlines, parsed_text_splitlines))
            with open(diff_name + '.html', mode='w', encoding='utf-8') as file:
                file.writelines(result)

    def test_xml_are_equal(self):
        """
        processa i file e li confronta
        :return:
        """

        path_diff = self.path_diff + '/xml/'
        del_and_make_dir(path_diff + '/OK')
        del_and_make_dir(path_diff + '/ko')

        # for parsed_xml, ddl_text, nome_file in build_parsed_docs(self.path_in):
        for parsed_xml, ddl_text, nome_file in get_parsed_docs():
            with self.subTest(i=nome_file.replace('.', '_')):
                # try:
                # leggo il file XML dal Dataset di test
                file_name = f'{self.path_out}/{nome_file}{".xml"}'
                with open(file_name, encoding='utf-8') as file:
                    orig_xml = file.read()
                print_out(f"XML equal per il file: {file_name}")

                # confronto tra il DDL_XML e il PARSED_XML
                risultato = False
                try:
                    self.assertEqual(parsed_xml, orig_xml, 'Test del file: ' + file_name)
                    risultato = True
                except AssertionError as e:
                    raise e
                finally:
                    self.make_write_diff_file(ddl_text, nome_file, orig_xml, parsed_xml, path_diff, risultato)

    def test_text_are_equal(self):
        """
        processa i file e confronta il solo testo: serve per capire se il parsing si "mangia" qualche parte
        :return:
        """

        def strip_tags(xml: str) -> str:
            """
            Elimina i tag (preservando il numero articolo)
            :param xml:
            :return:
            """
            #elimina i tag con il numero articolo e consierva il solo numero
            xml = re.sub(r'<a:\w*\s+numero="(?P<NUM>.*?)"[^>]*>', r'\g<NUM>', xml, flags=re.M | re.I | re.DOTALL)

            # cancella gli elementi CDATA: <![CDATA[{txt[:idx]}]]>
            xml = re.sub(r'<!\[CDATA\[(?P<TEXT>.*?)\]\]>', r'\g<TEXT>', xml, flags=re.M | re.I | re.DOTALL)

            # elimina, quindi, tutti gli altri tag
            xml = re.sub(r'<[^>]*>', r'', xml, flags=re.M | re.I | re.DOTALL)
            return xml

        path_diff = self.path_diff + '/text'
        del_and_make_dir(path_diff + '/OK')
        del_and_make_dir(path_diff + '/ko')

        for parsed_xml, ddl_text, nome_file in get_parsed_docs():
            with self.subTest(i=nome_file.replace('.', '_')):
                # try:
                # leggo il file XML dal Dataset di test
                file_name = f'{self.path_out}/{nome_file}{".xml"}'
                with open(file_name, encoding='utf-8') as file:
                    orig_xml = file.read()

                print_out(f"TXT equality per il file: {file_name}")

                # confronto tra il DDL_XML e il PARSED_XML
                parsed_xml = strip_tags(parsed_xml)
                orig_xml = strip_tags(orig_xml)
                risultato = False
                try:
                    # Ricava l'MD5 del solo testo presente e controlla se c'è tutto il testo
                    md5_1 = hashlib.md5(
                        re.sub(r'\s+', r'', parsed_xml, flags=re.M | re.I | re.DOTALL).encode()).hexdigest()
                    md5_2 = hashlib.md5(
                        re.sub(r'\s+', r'', orig_xml, flags=re.M | re.I | re.DOTALL).encode()).hexdigest()
                    self.assertEqual(md5_1, md5_2, 'Test del file: ' + file_name)
                    risultato = True
                except AssertionError as e:
                    raise e
                finally:
                    self.make_write_diff_file(ddl_text, nome_file, orig_xml, parsed_xml, path_diff, risultato)


