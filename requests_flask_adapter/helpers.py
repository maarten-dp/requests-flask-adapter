import requests

from .adapter import FlaskAdapter


class Session(requests.Session):
    additional_mounts = {}

    def __init__(self, keep_http_mounts=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for prefix, app in self.additional_mounts.items():
            self.mount(prefix, FlaskAdapter(app))

    @classmethod
    def register(cls, prefix, app):
        cls.additional_mounts[prefix] = app


def patch_requests(mounts):
    requests.Session = Session
    for prefix, app in mounts:
        Session.register(prefix, app)
