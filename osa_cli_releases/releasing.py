from datetime import datetime
import glob
import shutil
import subprocess
import tempfile
from dulwich.repo import Repo  # dulwich
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
        print("Working on %s" % filename)
        bump_upstream_repos_sha_file(filename)


def find_yaml_files(path):
    """ Lists all the yml files in a specific path
    :param path: Folder location
    :returns: List of files matching the glob
    """
    return glob.glob(path + "/*.yml")


def bump_upstream_repos_sha_file(filename):
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


def update_ansible_role_requirements_file(**kwargs):
    """ Updates the SHA of each of the ansible roles based on branch given in argument
    If branch is master, set a sha for the external roles.
    Else, stable branches only get openstack roles bumped.
    Copies all the release notes of the roles at the same time.
    """
    openstack_roles, external_roles, all_roles = sort_roles(kwargs["file"])
    if kwargs["os-branch"] == "master":
        for role in external_roles:
            index = all_roles.index(role)
            all_roles[index]["version"] = get_sha_from_ref(role["src"], "master")
    elif kwargs["os-branch"] not in [
        "stable/ocata",
        "stable/pike",
        "stable/queens",
        "stable/rocky",
        "stable/stein",
    ]:
        raise ValueError("Branch not recognized %s" % kwargs["os-branch"])

    for role in openstack_roles:
        index = all_roles.index(role)
        all_roles[index]["version"], role_path = clone_role(
            role["src"], kwargs["os-branch"]
        )
        copy_role_releasenotes(role_path, "./")
        shutil.rmtree(role_path)
    with open(kwargs["file"], "w") as arryml:
        yaml.safe_dump(all_roles)


def sort_roles(ansible_role_requirements_file):
    """ Separate the openstack roles from the external roles
    :param ansible_role_requirements_file: Path to the a-r-r file
    :returns: 3-tuple: (list of openstack roles, list of external roles, list of all roles)
    """
    with open(ansible_role_requirements_file, "r") as arryml:
        all_roles = yaml.safe_load(arryml)
    external_roles = []
    openstack_roles = []
    for role in all_roles:
        if role["src"].startswith("https://git.openstack.org/"):
            openstack_roles.append(role)
        else:
            external_roles.append(role)
    return openstack_roles, external_roles, all_roles


def clone_role(url, branch):
    """ Git clone
    :param url: Source of the git repo
    :param branch: Branch of the git repo
    :returns: latest sha of the clone and its location
    """
    dirpath = tempfile.mkdtemp()
    subprocess.check_call(["git", "clone", url, "-b", branch, dirpath])
    repo = Repo(dirpath)

    return repo.head(), dirpath


def copy_role_releasenotes(src_path, dest_path):
    """ Copy release notes from src to dest
    """
    renos = glob.glob("{}/releasenotes/notes/*.yaml".format(src_path))
    for reno in renos:
        subprocess.call(
            ["rsync", "-aq", reno, "{}/releasenotes/notes/".format(dest_path)]
        )


def find_release_number():
    """ Find a release version amongst usual OSA files
    :returns: version (str),  filename containing version (string)
    """
    oa_version_files = [
        "inventory/group_vars/all/all.yml",
        "group_vars/all/all.yml",
        "playbooks/inventory/group_vars/all.yml",
    ]
    for filename in oa_version_files:
        try:
            with open(filename, "r") as vf:
                version = yaml.safe_load(vf)["openstack_release"]
                found_file = filename
                break
        except FileNotFoundError:
            pass
    else:
        raise FileNotFoundError("No file found matching the list of files")
    return version, found_file


def next_release_number(current_version, releasetype):
    version = current_version.split(".")
    if releasetype in ("milestone", "rc"):
        increment_milestone_version(version, releasetype)
    else:
        increment = {"bugfix": (0, 0, 1), "feature": (0, 1, 0)}[releasetype]
        increment_version(version, increment)


# THis is taken from releases repo
def increment_version(old_version, increment):
    """Compute the new version based on the previous value.
    :param old_version: Parts of the version string for the last
                        release.
    :type old_version: list(str)
    :param increment: Which positions to increment.
    :type increment: tuple(int)
    """
    new_version_parts = []
    clear = False
    for cur, inc in zip(old_version, increment):
        if clear:
            new_version_parts.append("0")
        else:
            new_version_parts.append(str(int(cur) + inc))
            if inc:
                clear = True
    return new_version_parts


# THis is taken from releases repo
def increment_milestone_version(old_version, release_type):
    """Increment a version using the rules for milestone projects.
    :param old_version: Parts of the version string for the last
                        release.
    :type old_version: list(str)
    :param release_type: Either ``'milestone'`` or ``'rc'``.
    :type release_type: str
    """
    if release_type == "milestone":
        if "b" in old_version[-1]:
            # Not the first milestone
            new_version_parts = old_version[:-1]
            next_milestone = int(old_version[-1][2:]) + 1
            new_version_parts.append("0b{}".format(next_milestone))
        else:
            new_version_parts = increment_version(old_version, (1, 0, 0))
            new_version_parts.append("0b1")
    elif release_type == "rc":
        new_version_parts = old_version[:-1]
        if "b" in old_version[-1]:
            # First RC
            new_version_parts.append("0rc1")
        else:
            next_rc = int(old_version[-1][3:]) + 1
            new_version_parts.append("0rc{}".format(next_rc))
    else:
        raise ValueError("Unknown release type {!r}".format(release_type))
    return new_version_parts


def update_release_number(filename, version):
    yaml = YAML()
    with open(filename, "r") as versionfile:
        y = yaml.load(versionfile)
    y["openstack_version"] = version
    with open(filename, "w") as versionfile:
        yaml.dump(y, versionfile)
