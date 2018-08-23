import requests  # From requests
import requirements as pyrequirements  # From requirements-parser
import yaml  # From PyYAML
from prettytable import PrettyTable  # From prettytable


def parse_requirements(requirements):
    """Parse requirement file contents into name, constraints specs, and extra data
    :param pin: Complete string containing a requirement
    :returns: A detailed requirement, each requirement being a tuple containing:
                 - package 'name' (string)
                 - package 'specs' (list of tuples)
                 - package 'extras' (list)
    """
    for req in pyrequirements.parse(requirements):
        yield req


def get_pypi_versions(pins):
    """ Display package metadata on PyPI
    :param pins: this is a list of packages to check on PyPI
    :returns: dict whose keys are package names and value is latest package version)
    """
    versions = {}
    for pkgname in pins:
        versions[pkgname] = get_pypi_version(pkgname)
    return versions


def get_pypi_version(name):
    """ Return latest version of a package on PyPI
    :param name: This is the project name on PyPI
    :returns: String containing latest version of package
    """
    r = requests.get("https://pypi.org/pypi/{name}/json".format(name=name))
    return r.json()["info"]["version"]


def parse_upper_constraints(sha):
    """ Parses openstack upstream upper-constraints file into name, constraints specs, and extra data.
    :param sha: The SHA of the openstack requirements used to fetch the upper constraints file
    :returns: A detailed requirement, each requirement being a tuple containing:
                 - package 'name' (string)
                 - package 'specs' (list of tuples)
                 - package 'extras' (list)
    """
    url = "https://raw.githubusercontent.com/openstack/requirements/{}/upper-constraints.txt".format(
        sha
    )
    response = requests.get(url)
    for req in pyrequirements.parse(response.text):
        yield req


def discover_requirements_sha(
    path="playbooks/defaults/repo_packages/openstack_services.yml"
):
    """ Finds in openstack-ansible repos the current SHA for the requirements repo
    :param path: Location of the YAML file containing requirements_git_install_branch
    :returns: String containing the SHA of the requirements repo.
    """
    with open(path, "r") as os_repos_yaml:
        repos = yaml.safe_load(os_repos_yaml)
    return repos["requirements_git_install_branch"]


def print_requirements_state(pins, latest_versions, constraints_versions):
    """ Shows current status of global-requirement-pins.txt
    :param pins: A dict containing requirements of the current global-requirement-pins file
    :param latest_versions: A dict containing the latest version of each requirement in pypi
    :param constraints_version: A dict containing the current version of all constraints from requirements repo
    :returns: Nothing
    """
    table = PrettyTable(
        ["Package", "Current Version Spec", "Latest version on PyPI", "Constrained to"]
    )
    for pkgname in pins.keys():
        table.add_row(
            [
                pkgname,
                " ".join(*pins[pkgname]),
                latest_versions[pkgname],
                constraints_versions.get(pkgname, "None"),
            ]
        )
    print(table)
