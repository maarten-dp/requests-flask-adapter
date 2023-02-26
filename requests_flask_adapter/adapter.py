from io import BytesIO

from urllib3.response import HTTPResponse
from requests.adapters import BaseAdapter, HTTPAdapter
from flask.testing import EnvironBuilder
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
    def __init__(self, app, base_url=None):
        self.app = app
        self.environ_base = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "RequestsFlask/0.0.1",
        }
        self.base_url = base_url

    def send(self, request, **kwargs):
        kw = {
            "environ_base": self.environ_base,
            "method": request.method,
            "data": request.body,
            "headers": request.headers.items(),
        }
        builder = EnvironBuilder(app=self.app, path=request.path_url, **kw)
        if self.base_url:
            builder.base_url = self.base_url

        try:
            environ = builder.get_environ()
        finally:
            builder.close()

        rv = run_wsgi_app(self.app, environ, buffered=True)
        return self.build_response(request, rv)

    def build_response(self, request, rv):
        content, status, headers = rv
        if content:
            fh = BytesIO(content[0])
            for chunk in content:
                fh.write(chunk)
            fh.seek(0)
            content = fh
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
            original_response=MockResponse(headers),
        )

        return HTTPAdapter.build_response(self, request, resp)

    def close(self):
        pass
