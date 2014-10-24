from flask import Flask

app = Flask(__name__)

app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SECRET_KEY'] = b'development key'
app.config['DB'] = ''

app.config.from_envvar('APP_CFG')

from . import views
from . import utils
