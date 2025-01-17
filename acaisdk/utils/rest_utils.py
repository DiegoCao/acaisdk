import urllib3
import requests
from http import HTTPStatus
from acaisdk.utils import exceptions
from requests_futures.sessions import FuturesSession

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = None


def get_session() -> requests.Session:
    global SESSION
    if not SESSION:
        SESSION = requests.Session()
    return SESSION


def post(server, port, service, path,
         params: dict, data: dict, file=None):
    r = get_session().post('http://{}:{}/{}/{}'
                           .format(server, port, service, path),
                           data=params,
                           json=data,
                           verify=False)
    if r.status_code != HTTPStatus.OK:
        raise exceptions.RemoteException(r.content)
    if path == 'change_status':
        return
    return r.json()


def get(server, port, service, path, params: dict):
    r = get_session().get('http://{}:{}/{}/{}'
                          .format(server, port, service, path),
                          params=params, verify=False)
    if r.status_code != HTTPStatus.OK:
        raise exceptions.RemoteException(r.content)
    return r.json()

def async_post(server, port, service, path,
         params: dict, data: dict, file=None):
    session = FuturesSession()

    r = session.post('http://{}:{}/{}/{}'
                           .format(server, port, service, path),
                           data=params,
                           json=data,
                           verify=False)
    return r
