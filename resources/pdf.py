import re

import weasyprint
from flask import Blueprint, abort, make_response, request

from logging_config import logger

pdf_api = Blueprint('pdf_api', __name__)


# Regex pattern for validating filenames
FILENAME_PATTERN = r'^[\w\-. ]+$'


def validate_filename(filename: str) -> bool:
    """
    Validates a filename for use in the Content-Disposition header
    """
    return bool(re.fullmatch(FILENAME_PATTERN, filename))


@pdf_api.route('/api/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    """
    Converts HTML to PDF and returns the PDF as a response

    Note:
        Use @page css to set the page size and orientation

    Request data:
        html (str): The HTML data to be converted
        filename (str, optional): The filename to use for the PDF (default: "converted")

    Returns:
        A response with the PDF data and the appropriate Content-Type and Content-Disposition headers
    """
    if not request.is_json:
        abort(400, 'No JSON data provided')

    # Get the HTML data and filename from the request
    data = request.get_json(silent=True)
    html = data.get('html')
    filename = data.get('filename', 'converted')

    if not html:
        abort(400, 'No HTML data provided')
    if not validate_filename(filename):
        abort(400, 'Invalid filename')

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
        abort(500, 'Error converting HTML to PDF: {}'.format(str(e)))
