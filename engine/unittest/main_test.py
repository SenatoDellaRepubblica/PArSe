from engine.misc.misc import pretty_print_xml, read_text_with_enc
from engine.misc.converter import taf_to_normal_form
from flask import Flask

app = Flask(__name__)

@app.route('/')
def show():
    html_text = read_text_with_enc(r"..\..\..\test2\taf.htm")
    html_text = taf_to_normal_form(html_text)
    return html_text[0]


if __name__ == '__main__':
    app.run()
