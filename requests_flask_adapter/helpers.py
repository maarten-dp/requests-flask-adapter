import requests

from .adapter import FlaskAdapter


class Session(requests.Session):
    additional_mounts = {}

    def __init__(self, keep_http_mounts=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for prefix, (app, base_url) in self.additional_mounts.items():
            self.mount(prefix, FlaskAdapter(app, base_url=base_url))

    @classmethod
    def register(cls, prefix, app, base_url=None):
        cls.additional_mounts[prefix] = (app, base_url)


def patch_requests(mounts):
    requests.Session = Session
    for args in mounts:
        Session.register(*args)
