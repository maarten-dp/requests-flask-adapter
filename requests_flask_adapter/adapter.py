from io import BytesIO

from urllib3.response import HTTPResponse
from requests.adapters import BaseAdapter, HTTPAdapter
from flask.testing import make_test_environ_builder
from werkzeug.test import run_wsgi_app


class MockHeaders:
    def __init__(self, headers):
        self._headers = headers

    def get_all(self, name, default):
        return self._headers.get_all(name) or default


class MockResponse:
    def __init__(self, headers):
        self.msg = MockHeaders(headers)

    def isclosed(self, *args, **kwargs):
        return True


class FlaskAdapter(BaseAdapter):
    def __init__(self, app):
        self.app = app
        self.environ_base = {
            'REMOTE_ADDR': "127.0.0.1",
            'HTTP_USER_AGENT': 'RequestsFlask/0.0.1'
        }

    def send(self, request, **kwargs):
        kw = {
            'environ_base': self.environ_base,
            'method': request.method,
            'data': request.body,
            'headers': request.headers.items()
        }
        builder = make_test_environ_builder(self.app, request.path_url, **kw)

        try:
            environ = builder.get_environ()
        finally:
            builder.close()

        rv = run_wsgi_app(self.app, environ, buffered=True)
        return self.build_response(request, rv)

    def build_response(self, request, rv):
        content, status, headers = rv
        if content:
            content = BytesIO(content[0])
        else:
            content = BytesIO()
        code, reason = status.split(None, 1)
        resp = HTTPResponse(
            body=content,
            headers=headers,
            status=int(code),
            version=10,
            reason=reason,
            preload_content=False,
            original_response=MockResponse(headers)
        )

        return HTTPAdapter.build_response(self, request, resp)

    def close(self):
        pass
