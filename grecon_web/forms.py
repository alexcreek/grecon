from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import InputRequired

class SearchForm(Form):
    country = TextField('country', validators=[InputRequired()])

