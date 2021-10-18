import re
from unittest import TestCase

import config
from engine.unittest.unittest_utils import get_parsed_docs


class TestConsistency(TestCase):
    """
    Effettua dei test di consistenza dell'articolato
    """

    @classmethod
    def setUpClass(cls):
        cls.path_in = config.UNITTEST_PATH_IN

    def test_h_p_vuoti(self):
        """
        Controlla che non vi siano <H:P></H:P> vuoti
        :return:
        """

        if get_parsed_docs() is None:
            self.fail('Lista documenti vuota')

        for parsed_xml, _, nome_file in get_parsed_docs():
            # try:
            with self.subTest(i=nome_file.replace('.', '_')):
                m = re.search(r'<h:p>\s*</h:p>', parsed_xml, flags=re.I | re.MULTILINE | re.DOTALL)
                self.assertIsNone(m)
                # except:
                #    self.fail("Failed with %s" % traceback.format_exc())

    def test_testo_in_chiusura_apertura(self):
        """
        Controlla che non via sia del testo tra la chiusura di un TAG e l'apertura di un altro
        :return:
        """

        if get_parsed_docs() is None:
            self.fail('Lista documenti vuota')

        for parsed_xml, _, nome_file in get_parsed_docs():
            # try:
            with self.subTest(i=nome_file.replace('.', '_')):
                regex = r"</a:[^>]*>([^<]+)<a:"
                matches = re.finditer(regex, parsed_xml, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                text = ''
                for match in matches:
                    seg = match.group(1).strip()
                    if len(seg) > 0:
                        text = text + '\n' + '*' * 20 + '\n' + seg

                if len(text) > 0:
                    self.fail(msg=f"Testo trovato: {text}")
                    # except:
                    #    self.fail("Failed with %s" % traceback.format_exc())

    def test_novelle_after_articolo(self):
        """
        controlla che il tag novella sia contenuto dentro <ARTICOLO>
        :return:
        """

        if get_parsed_docs() is None:
            self.fail('Lista documenti vuota')

        for parsed_xml, _, nome_file in get_parsed_docs():
            with self.subTest(i=nome_file.replace('.', '_')):
                start_articolo = None
                start_novella = None
                m = re.search(r'<a:Articolo[^>]*?>', parsed_xml, flags=re.I | re.MULTILINE | re.DOTALL)
                if m:
                    start_articolo = m.start()

                m = re.search(r'<a:Novella[^>]*?>', parsed_xml, flags=re.I | re.MULTILINE | re.DOTALL)
                if m:
                    start_novella = m.start()

                if start_novella and start_articolo:
                    self.assertGreater(start_novella, start_articolo)
                else:
                    if not start_novella:
                        self.skipTest("Non è presente alcuna novella")
                    elif not start_articolo:
                        self.skipTest("Non è presente l'articolo")
                    else:
                        self.skipTest("Motivo indeterminato")

    def test_articolo_before_all(self):
        """
        controlla che il tag iniziale sia <ARTICOLO> o <CAPO> o <TITOLO>
        :return:
        """

        if get_parsed_docs() is None:
            self.fail('Lista documenti vuota')

        for parsed_xml, _, nome_file in get_parsed_docs():
            with self.subTest(i=nome_file.replace('.', '_')):
                # try:
                m = re.search(r'<a:Articolo[^>]*?>', parsed_xml, flags=re.I | re.MULTILINE | re.DOTALL)
                if m:
                    start = m.start()
                    m = re.search(r'<a:(:?<CAPT>[^>]*?)>', parsed_xml[start:],
                                  flags=re.I | re.MULTILINE | re.DOTALL)
                    if m and m.group('CAPT') and m.start() > start:
                        capt = m.group('CAPT').lower()
                        self.assertTrue(capt.startswith('comma') or
                                        capt.startswith('lettera') or
                                        capt.startswith('numero') or
                                        capt.startswith('novella'), 'Il primo tag non è nella sequenza corretta')
                else:
                    self.fail("il Tag Articolo non è stato trovato!")
                    # except:
                    #    self.fail("Failed with %s" % traceback.format_exc())