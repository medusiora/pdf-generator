import time
import os
import re
import shutil
import subprocess
import uuid

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


def compress_pdf(pdf: bytes, power=0, resolution=300) -> bytes:
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

    rand = str(uuid.uuid4())
    temp_name = 'temp-{}.pdf'.format(rand)
    temp_compressed_name = 'temp-compressed-{}.pdf'.format(rand)

    # Create a temporary file to store the PDF data
    with open(temp_name, 'wb') as f:
        f.write(pdf)

    # Compress the PDF using GhostScript
    subprocess.run([
        gs_path,
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS={}'.format(quality[power]),
        '-dDetectDuplicateImages=true',
        '-dDownsampleColorImages=true -dDownsampleGrayImages=true -dDownsampleMonoImages=true',
        '-dColorImageResolution={} -dGrayImageResolution={} -dMonoImageResolution={}'.format(
            resolution, resolution, resolution),
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        '-sOutputFile={}'.format(temp_compressed_name),
        temp_name
    ])

    # Read the compressed PDF data
    with open(temp_compressed_name, 'rb') as f:
        compressed_pdf = f.read()

    print('---------------------------------------------------------')
    print(temp_name)
    print(temp_compressed_name)
    print('Compression power: {} - {} Resolution {}'.format(power,
          quality[power], resolution))
    print('Compressed PDF size: {} KB'.format(len(compressed_pdf) / 1024))
    print('Original PDF size: {} KB'.format(len(pdf) / 1024))
    print('Compression ratio: {}%'.format(
        100 - (len(compressed_pdf) / len(pdf) * 100)))

    # Delete the temporary files
    os.remove(temp_name)
    os.remove(temp_compressed_name)

    return compressed_pdf


def create_pdf(html: str) -> bytes:
    """
    Converts HTML to PDF and returns the PDF data

    Args:
        html (str): The HTML data to be converted
        filename (str): The filename to use for the PDF

    Returns:
        The PDF data
    """
    # Sanitize the HTML to prevent XSS attacks
    html = sanitize_html(html)

    # Convert the HTML to PDF
    pdf = weasyprint.HTML(string=html).write_pdf(
        optimize_size=('fonts', 'images'),
    )

    return pdf


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

    try:
        # Convert the HTML to PDF
        pdf = create_pdf(html)

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
        power (int, optional): The compression power to use (default: 4) (0: /default, 1: /prepress, 2: /printer, 3: /ebook, 4: /screen)
        resolution (int, optional): The resolution to use for images (default: 300)
        retries (int, optional): The maximum number of times to retry the conversion (default: 0 No retries)

    Returns:
        A response with the compressed PDF data and the appropriate Content-Type and Content-Disposition headers
    """
    if not request.is_json:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Get the HTML data and filename from the request
    data = request.get_json(silent=True)
    html = data.get('html')
    filename = data.get('filename', 'converted')
    power = data.get('power', 4)
    resolution = data.get('resolution', 300)

    if not html:
        return jsonify({'error': 'No HTML data provided'}), 400

    # Validate the filename
    if not validate_filename(filename):
        return jsonify({'error': 'Invalid filename'}), 400

    max_retries = data.get('retries', 0)
    retry_count = 0

    while retry_count <= max_retries:
        try:
            # Convert the HTML to PDF
            pdf = create_pdf(html)

            # Compress the PDF
            pdf = compress_pdf(pdf, power=power, resolution=resolution)

            # Create a response with the compressed PDF data
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(
                filename)

            logger.info('Converted HTML to PDF from IP: {}'.format(
                request.remote_addr))

            return response

        except Exception as e:
            if retry_count < max_retries:
                # Retry the conversion
                retry_count += 1
                logger.warning(
                    'Retrying HTML to PDF conversion (Retry {}/{}): {}'.format(retry_count, max_retries, str(e)))
                time.sleep(1)  # Wait for a short time before retrying
            else:
                # If max retries reached, log the error and return an error response
                logger.error('Error converting HTML to PDF after {} retries from IP: {}, Reason: {}'.format(
                    max_retries, request.remote_addr, str(e)))
                return jsonify({'error': 'Error converting HTML to PDF after {} retries: {}'.format(max_retries, str(e))}), 500

    return jsonify({'error': 'Max retry count exceeded'}), 500
