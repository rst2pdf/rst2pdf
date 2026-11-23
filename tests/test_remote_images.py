"""Images referenced by URL are downloaded with a usable file extension (#1314)."""

import http.server
import os
import threading

import pytest

from rst2pdf.createpdf import RstToPdf
from rst2pdf.image import retrieve_image

SVG = os.path.join(os.path.dirname(__file__), 'input', 'warning.svg')


class ImageHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        with open(SVG, 'rb') as fh:
            body = fh.read()
        content_type = (
            'text/plain' if self.path.startswith('/plain') else 'image/svg+xml'
        )
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def server_url():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), ImageHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:%d' % server.server_port
    server.shutdown()
    server.server_close()


@pytest.mark.parametrize(
    'path, extension',
    [
        # no extension in the URL: taken from the Content-Type
        ('/badge', '.svg'),
        # the URL names a file that isn't an image: taken from the Content-Type
        ('/workflows/ci.yml?branch=main', '.svg'),
        # the URL's own extension wins, and the query string is ignored
        ('/plain/badge.svg?branch=main', '.svg'),
        # nothing to go on
        ('/plain/badge', ''),
    ],
)
def test_retrieve_image_keeps_extension(server_url, path, extension):
    filename = retrieve_image(server_url + path)
    try:
        assert os.path.splitext(filename)[1] == extension
        with open(filename, 'rb') as fh, open(SVG, 'rb') as expected:
            assert fh.read() == expected.read()
    finally:
        os.unlink(filename)


def test_remote_svg_is_rendered(server_url, tmp_path, caplog):
    pytest.importorskip('svglib')
    output = tmp_path / 'out.pdf'
    text = '.. image:: %s/badge\n\n.. image:: %s/badge.svg?branch=main\n' % (
        server_url,
        server_url,
    )

    RstToPdf().createPdf(text=text, output=str(output))

    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert errors == []
    assert output.stat().st_size > 0
