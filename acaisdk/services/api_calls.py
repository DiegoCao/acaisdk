from collections import namedtuple
from enum import Enum, auto
from acaisdk import configs
from acaisdk.utils import rest_utils
from acaisdk.utils.utils import *
from acaisdk.utils.exceptions import *
from acaisdk.credentials import get_credentials, has_logged_in
import json
import os

E = namedtuple('E', ['id', 'method'])


class RestMethods(Enum):
    get = auto()
    post = auto()
    async_post = auto()


class EnumFactory(Enum):
    @classmethod
    def GET(cls):
        return E(auto(), RestMethods.get)

    @classmethod
    def POST(cls):
        return E(auto(), RestMethods.post)

    @classmethod
    def ASYNC_POST(cls):
        return E(auto(), RestMethods.async_post)


class Services(Enum):
    @property
    def service_name(self):
        return {
            CredentialApi: 'credential',
            StorageApi: 'storage',
            MetadataApi: 'meta',
            JobRegistryApi: 'job_registry',
            JobSchedulerApi: 'job_scheduler',
            JobMonitorApi: 'job_monitor',
            ProvenanceApi: 'provenance',
            ProfilerApi: 'profiler',
            AutoProvisionerApi: 'auto_provisioner',
            LogServerApi: 'log_server',
            AutoMLApi: 'automl',
            SparkTunerAcceptApi: 'accept',
            SparkTunerTuneApi: 'cluster'
        }[type(self)]

    @property
    def endpoint(self):
        """There is only one endpoint the client talks to."""
        conf = configs.get_configs()
        cluster = os.environ.get('CLUSTER', None)
        if cluster == 'PHOEBE':
            return conf.private_cred_endpoint, conf.private_cred_endpoint_port
        # running within the pods created by phoebe
        if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/namespace'):
            with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace','r') as f:
                namespace=f.read()
                if namespace == 'default':
                    return conf.cred_endpoint, conf.cred_endpoint_port
                return conf.private_cred_endpoint, conf.private_cred_endpoint_port
        return conf.cred_endpoint, conf.cred_endpoint_port

    @property
    def method(self):
        return self.value.method


class CredentialApi(Services):
    create_project = EnumFactory.POST()
    create_user = EnumFactory.POST()
    resolve_user_id = EnumFactory.GET()
    resolve_project_id = EnumFactory.GET()


class StorageApi(Services):
    # File system, deprecated
    list_directory = EnumFactory.GET()
    make_directory = EnumFactory.POST()
    upload_file = EnumFactory.POST()
    change_status = EnumFactory.POST()
    download_file = EnumFactory.GET()
    download_files = EnumFactory.POST()
    list_file_versions = EnumFactory.GET()
    finish_upload = EnumFactory.POST()

    # File system v2
    start_file_upload_session = EnumFactory.POST()
    poll_file_upload_session = EnumFactory.GET()
    finish_file_upload_session = EnumFactory.POST()
    abort_file_upload_session = EnumFactory.POST()

    # File Set
    create_file_set = EnumFactory.POST()
    resolve_file_set = EnumFactory.GET()
    resolve_vague_path = EnumFactory.GET()
    download_file_set = EnumFactory.GET()
    list_file_set_versions = EnumFactory.GET()
    list_file_sets = EnumFactory.GET()


class JobRegistryApi(Services):
    new_job = EnumFactory.POST()
    job = EnumFactory.GET()
    jobs = EnumFactory.GET()


class JobSchedulerApi(Services):
    new_job = EnumFactory.POST()


class JobMonitorApi(Services):
    job_status = EnumFactory.POST()


class MetadataApi(Services):
    get_meta = EnumFactory.POST()

    # File metadata
    update_file_meta = EnumFactory.POST()
    del_file_meta = EnumFactory.POST()

    # File set metadata
    update_file_set_meta = EnumFactory.POST()
    del_file_set_meta = EnumFactory.POST()

    # Job Metadata
    update_job_meta = EnumFactory.POST()
    del_job_meta = EnumFactory.POST()

    # Query
    query_meta = EnumFactory.POST()


class LogServerApi(Services):
    get_job_log = EnumFactory.GET()


class ProfilerApi(Services):
    register_template = EnumFactory.POST()
    similar_job = EnumFactory.GET()


class AutoProvisionerApi(Services):
    new_job = EnumFactory.POST()


class ProvenanceApi(Services):
    register = EnumFactory.POST()

class AutoMLApi(Services):
    tasks = EnumFactory.POST()
    submit_model = EnumFactory.POST()
    get_status = EnumFactory.GET()

class AutoMLApi(Services):
    tasks = EnumFactory.POST()
    submit_model = EnumFactory.POST()
    get_status = EnumFactory.GET()

class SparkTunerAcceptApi(Services):
    job = EnumFactory.POST()
    getstatus = EnumFactory.POST()

class SparkTunerTuneApi(Services):
    tunejob = EnumFactory.ASYNC_POST()

class RestRequest:
    def __init__(self, service: Services):
        self.service = service
        self.query = {}
        self.data = {}
        self.credentials = {}

    def with_query(self, query: dict):
        self.query = query
        return self

    def with_data(self, data: dict):
        self.data = data
        return self

    def with_credentials(self, credentials: dict = None):
        """A bit dirty, maybe this class should not have visibility
        to credentials class.
        """
        if not credentials:
            self.credentials = get_credentials()
        else:
            self.credentials = credentials

        if not has_logged_in(self.credentials):
            _msg = 'You have not logged in to ACAI'
            raise AcaiException(_msg)

        return self

    def run(self):
        endpoint, port = self.service.endpoint
        debug('Running request:',
              endpoint,
              port,
              self.service.service_name,
              self.service.name)

        if self.service.method == RestMethods.get:
            self.query.update(self.credentials)
            debug('GET query', json.dumps(self.query))
            return rest_utils.get(endpoint,
                                  port,
                                  self.service.service_name,
                                  self.service.name,
                                  self.query)
        elif self.service.method == RestMethods.post:
            self.data.update(self.credentials)
            debug('POST data', json.dumps(self.data))
            print("----------- printing post data -------------")
            print(endpoint)
            print(port)
            return rest_utils.post(endpoint,
                                   port,
                                   self.service.service_name,
                                   self.service.name,
                                   self.query,
                                   self.data)
        elif self.service.method == RestMethods.async_post:
            self.data.update(self.credentials)
            debug('ASYNC POST data', json.dumps(self.data))
            return rest_utils.async_post(endpoint,
                                   port,
                                   self.service.service_name,
                                   self.service.name,
                                   self.query,
                                   self.data)
        raise AcaiException('Unknown request type: '
                            '{}'.format(self.service.method))


    def runCustomPath(self, pathStr):
        endpoint, port = self.service.endpoint
        debug('Running request:',
              endpoint,
              port,
              self.service.service_name,
              pathStr)

        if self.service.method == RestMethods.get:
            self.query.update(self.credentials)
            debug('GET query', json.dumps(self.query))
            return rest_utils.get(endpoint,
                                  port,
                                  self.service.service_name,
                                  pathStr,
                                  self.query)
        elif self.service.method == RestMethods.post:
            self.data.update(self.credentials)
            debug('POST data', json.dumps(self.data))
            return rest_utils.post(endpoint,
                                   port,
                                   self.service.service_name,
                                   pathStr,
                                   self.query,
                                   self.data)
        raise AcaiException('Unknown request type: '
                            '{}'.format(self.service.method))
