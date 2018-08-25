from datetime import datetime
import glob
import subprocess
import requests  # requests
import requirements as pyrequirements  # requirements-parser
import yaml  # PyYAML
from prettytable import PrettyTable  # prettytable
from ruamel.yaml import YAML  # ruamel.yaml


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


def bump_upstream_repos_shas(path):
    """ Processes all the yaml files in the path by updating their upstream repos shas
    :param path: String containing the location of the yaml files to update
    :returns: None
    """
    filelist = find_yaml_files(path)
    for filename in filelist:
        bump_upstream_repos_sha_file(filename)


def find_yaml_files(path):
    """ Lists all the yml files in a specific path
    :param path: Folder location
    :returns: List of files matching the glob
    """
    return glob.glob(path + "/*.yml")


def bump_upstream_repo_sha_file(filename):
    yaml = YAML()  # use ruamel.yaml to keep comments
    with open(filename, "r") as ossyml:
        repofiledata = yaml.load(ossyml)

    repos = build_repos_dict(repofiledata)
    for project, projectdata in repos.items():
        # Do not update if no branch to track
        if projectdata["trackbranch"] is not None:
            sha = get_sha_from_ref(projectdata["url"], projectdata["branch"])
            repofiledata[project + "_git_install_branch"] = sha
            repofiledata.yaml_add_eol_comment(
                "HEAD as of {:%d.%m.%Y}".format(datetime.now()),
                project + "_git_install_branch",
            )

    with open(filename, "w") as fw:
        yaml.dump(repofiledata, fw)


# def parse_repos_info(filename):
#    """ Take a file consisting of ordered entries
#    *_git_repo, followed by *_git_install_branch, with a comment the branch to track,
#    returns information about each repos.
#    :param filename: String containing path to file to analyse
#    :returns: YAMLMap object, an ordered dict keeping the comments.
#    """
#    yaml = YAML() # use ruamel.yaml to keep comments
#    with open(filename,'r') as ossyml:
#        y = yaml.load(ossyml)
#    return y


def build_repos_dict(repofiledict):
    """ Returns a structured dict of repos data
    :param repofiledict:
    :returns: Dict of repos, whose values are dicts containing shas and branches.
    """
    repos = dict()
    reponames = [
        key.replace("_git_repo", "")
        for key in repofiledict.keys()
        if key.endswith("_git_repo")
    ]
    for reponame in reponames:
        repos[reponame] = {
            "url": repofiledict[reponame + "_git_repo"],
            "sha": repofiledict[reponame + "_git_install_branch"],
            "trackbranch": repofiledict[reponame + "_git_track_branch"],
        }
    return repos


def get_sha_from_ref(repo_url, reference):
    """ Returns the sha corresponding to the reference for a repo
    :param repo_url: location of the git repository
    :param reference: reference of the branch
    :returns: utf-8 encoded string of the SHA found by the git command
    """
    # Using subprocess instead of convoluted git libraries.
    # Any rc != 0 will be throwing an exception, so we don't have to care
    out = subprocess.check_output(
        ["git", "ls-remote", "--exit-code", repo_url, reference]
    )
    # out is a b'' type string always finishing up with a newline
    # construct list of (ref,sha)
    refs = [
        (line.split(b"\t")[1], line.split(b"\t")[0])
        for line in out.split(b"\n")
        if line != b"" and b"^{}" not in line
    ]
    if len(refs) > 1:
        raise ValueError(
            "More than one ref for reference %s, please be more explicit %s"
            % (reference, refs)
        )
    return refs[0][1].decode("utf-8")


def find_next_tag(repo_url, tag):
    pass
