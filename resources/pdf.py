import weasyprint
from flask import Blueprint, abort, make_response, request

pdf_api = Blueprint('pdf_api', __name__)


@pdf_api.route('/api/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    """
    Converts HTML to PDF and returns the PDF as a response

    Note:
        Use @page css to set the page size and orientation
    """

    if not request.is_json:
        abort(400, 'No JSON data provided')

    # Get the HTML data from the request
    data = request.get_json(silent=True)
    html = data.get('html')
    filename = data.get('filename', 'converted')

    if not html:
        abort(400, 'No HTML data provided')

    try:

        # Convert the HTML to PDF
        pdf = weasyprint.HTML(string=html).write_pdf()

        # Create a response with the PDF data
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename={}.pdf'.format(
            filename)

        return response

    except Exception as e:
        abort(500, str(e))
