
from flask import Blueprint, render_template

main_api = Blueprint('main_api', __name__)


@main_api.route('/')
def index():
    return render_template('index.html')
