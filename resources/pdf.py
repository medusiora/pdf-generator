import re

import weasyprint
from flask import Blueprint, jsonify, make_response, request

from logging_config import logger
from middleware.auth import verify_api_key

pdf_api = Blueprint('pdf_api', __name__)


# Regex pattern for validating filenames
FILENAME_PATTERN = r'^[\w\-. ]+$'


def validate_filename(filename: str) -> bool:
    """
    Validates a filename for use in the Content-Disposition header
    """
    return bool(re.fullmatch(FILENAME_PATTERN, filename))


@pdf_api.route('/api/convert-to-pdf', methods=['POST'])
@verify_api_key
def convert_to_pdf():
    """
    Converts HTML to PDF and returns the PDF as a response

    Note:
        Use @page css to set the page size and orientation

    Request headers:
        API-key (str): The API key to use for authentication

    Request data:
        html (str): The HTML data to be converted
        filename (str, optional): The filename to use for the PDF (default: "converted")

    Returns:
        A response with the PDF data and the appropriate Content-Type and Content-Disposition headers
    """
    if not request.is_json:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Get the HTML data and filename from the request
    data = request.get_json(silent=True)
    html = data.get('html')
    filename = data.get('filename', 'converted')

    if not html:
        return jsonify({'error': 'No HTML data provided'}), 400
    if not validate_filename(filename):
        return jsonify({'error': 'Invalid filename'}), 400

    try:
        # Convert the HTML to PDF
        pdf = weasyprint.HTML(string=html).write_pdf()

        # Create a response with the PDF data
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename={}.pdf'.format(
            filename)

        logger.info('Converted HTML to PDF')

        return response

    except Exception as e:
        logger.error('Error converting HTML to PDF: {}'.format(str(e)))
        return jsonify({'error': 'Error converting HTML to PDF: {}'.format(str(e))}), 500
