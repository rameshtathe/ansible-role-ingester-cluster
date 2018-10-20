#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
from git import Repo

__author__ = 'rameshtathe'


def deploy_cluster_with_kafka_failure(environment, release_branch):
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'kafka' -p 'home/ubuntu/private_key' -s "
                    "all_services -t install,configure -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'kafka' -p 'home/ubuntu/private_key' -s kafka "
                    "-t execute -k 'create_topics' -o 'all' -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_master' -p 'home/ubuntu/private_key' "
                    "-s execute_spark_jobs -t execute -j 'all' -b '%s'" %
                    (environment, release_branch), shell=True)

def deploy_cluster_with_cluster_failure(environment, release_branch):
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_worker1' -p 'home/ubuntu/private_key' "
                    "-s all_services -t install,configure -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_worker2' -p 'home/ubuntu/private_key' "
                    "-s all_services -t install,configure -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_master' -p 'home/ubuntu/private_key' "
                    "-s all_services -t install,configure -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_master' -p 'home/ubuntu/private_key' "
                    "-s deploy_dc_ingester -t stop -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_master' -p 'home/ubuntu/private_key' "
                    "-s deploy_dc_ingester -t start -b '%s'" %
                    (environment, release_branch), shell=True)
    subprocess.call("/home/ubuntu/ansible-playbooks-opcito/run-playbook.sh "
                    "-e '%s' -c 'ingester_master' -p 'home/ubuntu/private_key' "
                    "-s execute_spark_jobs -t execute -j 'all' -b '%s'" %
                    (environment, release_branch), shell=True)

def clone_repository(repo_url):
    Repo.clone_from(repo_url, "/home/ubuntu/ansible-playbooks-opcito",
                    branch="features/store-profile")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            environment=dict(required=True, type='str'),
            component=dict(required=True, type='str'),
            ansible_branch=dict(required=True, type='str'),
            release_branch=dict(required=True, type='str'),
            ansible_repo_url=dict(required=True, type='str'),
        ),
        supports_check_mode=True,
    )

    clone_repository(module.params['ansible_repo_url'])
    if module.params['environment'] == 'staging' and \
                    module.params['component'] == 'kafka':
        deploy_cluster_with_kafka_failure(
            module.params['environment'], module.params['release_branch']
        )
        return module.exit_json(msg='Setup cluster successfully', changed=True)

    if module.params['environment'] == 'staging' and (
                        module.params['component'] == 'ingester_master' or
                        module.params['component'] == 'ingester_worker1' or
                    module.params['component'] == 'ingester_worker2'
    ):
        deploy_cluster_with_cluster_failure(
            module.params['environment'], module.params['release_branch']
        )
        return module.exit_json(msg='Setup cluster successfully', changed=True)

    return module.exit_json(changed=True)


if __name__ == "__main__":
    main()