from . import app
from jinja2 import Markup, escape

@app.template_filter()
def nl2br(text):
    return Markup(escape(text).replace('\n', Markup('<br>\n')))
