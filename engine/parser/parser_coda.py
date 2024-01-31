import re


class CodaParser(object):
    """
    Esegue il parsing della coda del documento
    """
    def __init__(self, testo: str):
        self.testo = testo

    def cancella_coda(self, tipo_testo: str):
        """
        Cancella la coda del documento

        :param tipo_testo: ddl, dl
        """
        # TODO: al momento elmina solo la coda dei DL
        if tipo_testo == "dl":
            self.testo = re.sub(r"^\s*Dato\s+a\s+Roma.*?add.*?Visto,\s+il\s+Guardasigilli:.*", r"", self.testo, flags= re.IGNORECASE | re.DOTALL | re.MULTILINE)

        return self.testo
