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


def bump_oa_release_number():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "release_type",
        choices=("bugfix", "feature", "milestone", "rc"),
        help="The type of release to generate",
        default="bugfix",
    )
    args = parser.parse_args()

    current_version, filename = releasing.find_release_number()
    print("Found version %s in %s" % (current_version, filename))
    next_version = releasing.next_release_number(current_version, args.release_type)
    print("Updating %s to %s" % (filename, next_version))
    releasing.update_release_number(filename, ".".join(next_version))
