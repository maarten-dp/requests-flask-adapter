import json
from io import StringIO

from pytest import fixture
from flask import Flask, request, Response
from requests_flask_adapter import Session
import requests

A_DICT = {
    'key1': 'val1',
    'key2': ['val2', 'val3']
}
AN_EXPECTED_DICT = {
    'key1': ['val1'],
    'key2': ['val2', 'val3']
}


@fixture(scope='function')
def app():
    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
    def echo(path):
        def get_file_content():
            fh = request.files.get('SomeFile.txt')
            if fh:
                return fh.read().decode('utf-8')

        resp = Response(json.dumps({
            'path': path,
            'args': request.args.to_dict(flat=False),
            'form': request.form.to_dict(flat=False),
            'json': request.json,
            'headers': dict(request.headers),
            'files': get_file_content(),
            'auth': request.authorization,
        }))

        resp.set_cookie(
            'view_count', str(int(request.cookies.get('view_count', 0)) + 1))
        return resp
    return app


@fixture(scope='function')
def session(app):
    Session.register('http://app', app)
    return Session()


def test_it_makes_a_simple_get_request(session):
    res = session.get('http://app/echo')
    assert res.json()['path'] == 'echo'


def test_it_makes_a_get_request_with_query_params(session):
    res = session.get('http://app/echo', params=A_DICT)
    assert res.json()['args'] == AN_EXPECTED_DICT


def test_it_makes_a_simple_post_request(session):
    res = session.post('http://app/echo', data=A_DICT)
    assert res.json()['form'] == AN_EXPECTED_DICT


def test_it_makes_a_json_post_request(session):
    res = session.post('http://app/echo', json=A_DICT)
    assert res.json()['json'] == A_DICT


def test_it_sends_headers(session):
    res = session.get('http://app/echo', headers={'X-SomeHeader': 'header'})
    assert res.json()['headers'] == {
        'User-Agent': 'python-requests/{}'.format(requests.__version__),
        'Host': 'localhost',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive', 
        'X-Someheader': 'header'
    }


def test_it_can_send_and_receive_cookies(session):
    res = session.get('http://app/echo')
    res = session.get('http://app/echo', cookies=res.cookies)
    assert int(res.cookies['view_count']) == 2


def test_it_can_send_files(session):
    content = 'Some content'
    fh = StringIO(content)
    res = session.post('http://app/echo', files={'SomeFile.txt': fh})
    assert res.json()['files'] == content


def test_it_can_send_basic_auth(session):
    res = session.post('http://app/echo', auth=('user', 'pass'))
    assert res.json()['auth'] == {'username': 'user', 'password': 'pass'}


def test_it_can_patch_requests(app):
    from requests_flask_adapter.helpers import patch_requests
    patch_requests([('http://patched_app', app)])
    from requests import Session
    res = Session().get('http://patched_app/echo')
    assert res.json()['path'] == 'echo'
