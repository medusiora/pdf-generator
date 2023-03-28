import os
import re
import shutil
import subprocess

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


def sanitize_html(html: str) -> str:
    """
    Sanitizes HTML to prevent XSS attacks
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    return str(soup)


def get_ghostscript_path():
    gs_names = ['gs', 'gswin32c', 'gswin64c']

    for gs_name in gs_names:
        try:
            gs_path = shutil.which(gs_name)
            if gs_path:
                return gs_path
        except Exception:
            pass

    raise Exception('GhostScript not found')


def compress_pdf(pdf: bytes, power=0) -> bytes:
    """
    Compresses a PDF using GhostScript

    Args:
        pdf (bytes): The PDF data to compress

    Returns:
        The compressed PDF data
    """

    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    gs_path = get_ghostscript_path()

    # Create a temporary file to store the PDF data
    with open('temp.pdf', 'wb') as f:
        f.write(pdf)

    # Compress the PDF using GhostScript
    subprocess.run([
        gs_path,
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS={}'.format(quality[power]),
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        '-sOutputFile=temp-compressed.pdf',
        'temp.pdf',
    ])

    # Read the compressed PDF data
    with open('temp-compressed.pdf', 'rb') as f:
        compressed_pdf = f.read()

    # Delete the temporary files
    os.remove('temp.pdf')
    os.remove('temp-compressed.pdf')

    return compressed_pdf


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

    # Validate the filename
    if not validate_filename(filename):
        return jsonify({'error': 'Invalid filename'}), 400

    # Sanitize the HTML to prevent XSS attacks
    html = sanitize_html(html)

    try:
        # Convert the HTML to PDF
        pdf = weasyprint.HTML(string=html).write_pdf(
            optimize_size=('fonts', 'images'),
        )

        # Create a response with the compressed PDF data
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(
            filename)

        logger.info('Converted HTML to PDF from IP: {}'.format(
            request.remote_addr))

        return response

    except Exception as e:
        # add ip address to log
        logger.error('Error converting HTML to PDF from IP: {}, Reason {}'.format(
            request.remote_addr, str(e)))
        return jsonify({'error': 'Error converting HTML to PDF: {}'.format(str(e))}), 500


@pdf_api.route('/api/v2/convert-to-pdf', methods=['POST'])
@verify_api_key
def convert_to_pdf_v2():
    """
    Converts HTML to PDF and returns the compressed PDF as a response

    Note:
        Use @page css to set the page size and orientation

    Request headers:
        API-key (str): The API key to use for authentication

    Request data:
        html (str): The HTML data to be converted
        filename (str, optional): The filename to use for the PDF (default: "converted")

    Returns:
        A response with the compressed PDF data and the appropriate Content-Type and Content-Disposition headers
    """
    if not request.is_json:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Get the HTML data and filename from the request
    data = request.get_json(silent=True)
    html = data.get('html')
    filename = data.get('filename', 'converted')

    if not html:
        return jsonify({'error': 'No HTML data provided'}), 400

    # Validate the filename
    if not validate_filename(filename):
        return jsonify({'error': 'Invalid filename'}), 400

    # Sanitize the HTML to prevent XSS attacks
    html = sanitize_html(html)

    try:
        # Convert the HTML to PDF
        pdf = weasyprint.HTML(string=html).write_pdf(
            optimize_size=('fonts', 'images'),
        )

        # Compress the PDF
        pdf = compress_pdf(pdf, power=4)

        # Create a response with the compressed PDF data
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(
            filename)

        logger.info('Converted HTML to PDF from IP: {}'.format(
            request.remote_addr))

        return response

    except Exception as e:
        # add ip address to log
        logger.error('Error converting HTML to PDF from IP: {}, Reason {}'.format(
            request.remote_addr, str(e)))
        return jsonify({'error': 'Error converting HTML to PDF: {}'.format(str(e))}), 500
