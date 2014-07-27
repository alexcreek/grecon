from flask_wtf import Form
from wtforms import StringField, SelectField
from wtforms.validators import InputRequired

class SearchForm(Form):
    search = StringField('search', validators=[InputRequired()])

#http://wtforms.simplecodes.com/docs/0.6/fields.html
class DropDown(Form):
    country = SelectField(u'Countries', coerce=str)
