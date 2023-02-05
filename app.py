from flask import Flask

from resources.main import main_api
from resources.pdf import pdf_api

app = Flask(__name__)

# Register the API blueprints
app.register_blueprint(main_api)
app.register_blueprint(pdf_api)


if __name__ == '__main__':
    app.run()
