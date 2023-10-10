from flask import Flask
import sentry_sdk

from resources.main import main_api
from resources.pdf import pdf_api


sentry_sdk.init(
    dsn="https://64bd10a83c0496888beb8b0be6bb2443@o1241713.ingest.sentry.io/4506024672624640",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
)


app = Flask(__name__)

# Register the API blueprints
app.register_blueprint(main_api)
app.register_blueprint(pdf_api)


if __name__ == '__main__':
    app.run()
