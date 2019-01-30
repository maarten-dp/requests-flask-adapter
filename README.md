[![Build Status](https://travis-ci.com/maarten-dp/requests-flask-adapter.svg?branch=master)](https://travis-ci.com/maarten-dp/requests-flask-adapter)

### Purpose

FlaskAdapter is a requests adapter intended to allow its user to call Flask app endpoints, with requests, without having to run a Flask server.

Its main uses include building integration tests and client tests without having to resort to multithreading/multiprocessing/running an instance in another shell/docker to spawn a running Flask app. In doing so, you are able to to call the endpoints you wish to test with your client. It can also be used as an alternative to the Flask test_client, unlocking the well-known and well-loved interface of requests in your unittests, because god knows I love those `json.loads(res.data.decode('utf-8'))` statements in my tests.

### Using FlaskAdapter as a test client

You can swap out the flask test client for a requests interface in two ways.

The first would be to import the requests_flask_adapter session, which is basically a session subclassed from a requests Session, but allows the registering of apps.

```python
from requests_flask_adapter import Session
from my_production_code import setup_my_app
from pytest import fixture

@fixture
def session():
    app = setup_my_app()
    Session.register('http://my_app', app)
    return Session()


def test_it_runs_my_test(session):
    result = session.get("http://my_app/my_endpoint", params={'some': 'params'})
    assert result.json() == {'nailed': 'it'}

```

if you don't want to or, for some reason, can't rely on the `requests_flask_adapter.Session`, you can also use the requests_flask_adapter helper function to monkey patch the requests Session. For now, it heavily depends on import order, so make sure to patch it before importing the Session for your tests.

```python
from requests_flask_adapter.helpers import patch_requests
patch_requests([
    ('http://patched_app', app),
    ('http://another_patched_app', another_app)
])

```

And in your tests you can now run code that imports the requests.Session

```python
def test_it_runs_code_that_imports_requests():
    result = my_code_that_imports_requests_and_does_something()
    assert result == [':ok_hand:']

```

### Using FlaskAdapter for client testing

Similarly, FlaskAdapter is very effective for testing a client that is written with requests.
And once again, without having to run a live server of your flask app.

```python
from requests_flask_adapter import Session
from my_production_code import setup_my_app, User
from my_client import Client
from pytest import fixture


@fixture
def client():
    app = setup_my_app()
    Session.register('http://my_app', app)
    return Client(
        base_url='http://my_app',
        session=Session(), # monkeypatch if your client isn't accepting another session.
        auth=('Scanlan', 'b3st_b4rd_Exandr!a'),
    )


def test_it_gets_a_user_list(client):
    users = client.users()
    assert users == ['vex', 'vax']


def test_it_can_upload_a_timesheet(client):
    with open('data/timesheet.xls', 'r') as fh:
        client.upload_timesheet(fh)
    user = User.query.get(1)
    assert user.hours_worked_this_month == 8

```

### Using FlaskAdapter for cross app integration tests

And just because I need to bloat this readme a bit to validate this project, I'm throwing in "integration testing" as one of its functionalities.
Of course, these integration tests require you to have access to the source code of the flask apps you're trying to test.

So, here's an example.

Let's assume the your team owns and maintains the following codebases:
 - A webshop application that's also keeping track of sales, users visited and other stats from the last hour. These stats are accessible though an endpoint in your app.
 - An ETL script that periodically runs and collects realtime stats from your webshop.
 - A timeseries database that stores the data extracted by your ETL script

Using the data stored in your timeseries database, you have a reporting script that you run once per month to determine peak hours, what product is most popular and during which hours, which amount of users showed interest in which products, which products are falling in and out of trending, etc.

Seeing as these codebases are still actively under construction, you want to make sure future implementations don't introduce regressions in the entire chain.

```python
from datetime import datetime, timedelta

from pytest import fixture
from requests_flask_adapter import Session
from my_webshop_app import app as feeder_app
from my_timeseries_database_app import app as timeseries_app, Series
from my_etl_project import (ETLWorker, FeederClient, TSWriter,
    ConfigLoader)

from .helpers import populate_webshop


Session.register('http://feeder_app', feeder_app)
Session.register('http://timeseries_app', timeseries_app)
populate_webshop(feeder_app)


@fixture
def feeder_client():
    config = ConfigLoader(location='environ')
    return FeederClient(
        base_url='http://feeder_app',
        session=Session(),
        username=config['feeder_username'],
        password=contig['feeder_password']
    )


@fixture
def writer():
    config = ConfigLoader(location='environ')
    return TSWriter(
        base_url='http://timeseries_app',
        session=Session(),
        username=config['writer_username'],
        password=contig['writer_password']
    )


def test_it_can_go_end_to_end(feeder_client, writer)
    now = datetime.now()
    worker = ETLWorker(
        feeder=feeder_client,
        writer=writer,
    )
    worker.run()
    result = Series.sum('my_serie_name', start=now, end=now + timedelta(days=1))
    assert result == 42

```

