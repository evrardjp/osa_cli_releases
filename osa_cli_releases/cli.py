import argparse
import osa_cli_releases.releasing as releasing


def analyse_global_requirement_pins():
    """Check a package list file for updates on PyPI or on upper constraints"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--requirements_sha",
        help="Sha used for fetching the upper constraints file in requirements",
    )
    parser.add_argument(
        "--file",
        help="path to global requirements pin file",
        default="global-requirement-pins.txt",
    )
    args = parser.parse_args()

    with open(args.file, "r") as global_req_file:
        pins = {
            pin.name: pin.specs
            for pin in releasing.parse_requirements(global_req_file.read())
        }

    latest_versions = releasing.get_pypi_versions(pins.keys())

    if not args.requirements_sha:
        sha = releasing.discover_requirements_sha()
    else:
        sha = args.requirements_sha

    constraints_versions = {
        pin.name: pin.specs for pin in releasing.parse_upper_constraints(sha)
    }
    releasing.print_requirements_state(pins, latest_versions, constraints_versions)


def bump_upstream_repos_shas():
    """ Bump upstream projects SHAs.
    :param path: String containing the path of the YAML files formatted for updates
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        help="path to the folder containing YAML files to update with new SHAs",
        default="playbooks/defaults/repo_packages/",
    )
    args = parser.parse_args()

    releasing.bump_upstream_repos_shas(args.path)


def bump_arr():
    """ Bump roles SHA and copies releases notes from the openstack roles.
    Also bumps roles from external sources when the branch to bump is master.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        help="path to ansible-role-requirements.yml file",
        default="ansible-role-requirements.yml",
    )
    parser.add_argument(
        "os-branch",
        help="Branch to use to find the role SHA for openstack roles. Master will also freeze external roles.",
    )
    args = parser.parse_args()
    releasing.update_ansible_role_requirements_file(filename=args['file'],branchname=args['os-branch'])


def freeze_arr():
    """ Freeze all roles shas for milestone releases.
    Bump roles SHA and copies releases notes from the openstack roles.
    Also freezes roles from external sources.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        help="path to ansible-role-requirements.yml file",
        default="ansible-role-requirements.yml",
    )
    args = parser.parse_args()
    releasing.freeze_ansible_role_requirements_file(filename=args['file'])

