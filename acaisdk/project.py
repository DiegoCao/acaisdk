from acaisdk.services.api_calls import *
from acaisdk import credentials
from acaisdk.private_cluster import get_private_cluster

class Project:
    @staticmethod
    def create_project(project_id: str,
                       admin_token: str,
                       project_admin: str,
                       csp: str='AWS',
                       budget: float=10) -> dict:
        """This is the starting point of your ACAI journey.
        Project, like its definition in GCP, is a bundle of resources. Users,
        files and jobs are only identifiable when ACAI system knows which
        project they are under.
        Use this method to create a project.
        :param project_id:
            Name of the project, it should be unique, as it is also the ID
            ACAI uses to identify a project.
        :param admin_token:
            One token to rule them all. This is the admin token to create
            new projects.
        :param project_admin:
            An user name for the project administrator.
        :param csp:
            Cloud Service provider that this project will be using
        :return:
            .. code-block::
                {
                  "admin_token": "string",
                  "project_id": "string",
                  "project_admin_name": "string"
                }
        """

        if budget == 10:
            print("Set the budget of Project {%s} to default value: $%.2f" %(project_id, budget))
            print("Update the budget using: set_budget(amount)")
        
        print('Cloud service provider: ', csp)

        if csp not in ['AWS', 'AZURE', 'GCP', 'PRIVATE']:
            print('CSP not supported: Current options: AWS, AZURE, GCP, PRIVATE')
            return

        resp = RestRequest(CredentialApi.create_project) \
            .with_data({'project_id': project_id,
                        'budget': budget,
                        'admin_token': admin_token,
                        'csp': csp,
                        "project_admin_name": project_admin}) \
            .run()
        
        # cloud service provider is private cluster, create bucket accordingly
        if csp == 'PRIVATE':
            print(resp)
            bucket_name = resp['bucket_name']
            private_cluster = get_private_cluster()
            private_cluster.create_buckets(bucket_name)
        
        return resp

    @staticmethod
    def create_user(project_id: str,
                    admin_token: str,
                    user: str,
                    login: bool = True) -> dict:
        """Create a new user for the project.
        :param project_id:
            Project ID.
        :param admin_token:
            Use the admin token you get from :py:meth:`~Project.create_project`
        :param user:
            Name for the new user.
        :param login:
            By default, automatically export the env variable and
            load the new credential.
        :return:
            .. code-block::
                {
                  "user_id": 0,
                  "user_token": "string"
                }
        """
        # Admin could be global or project admin
        r = RestRequest(CredentialApi.create_user) \
            .with_data({'project_id': project_id,
                        'admin_token': admin_token,
                        "user_name": user}) \
            .run()
        if login:
            credentials.login(r['user_token'])
            debug("Logged in with token {}".format(r['user_token']))
        return r