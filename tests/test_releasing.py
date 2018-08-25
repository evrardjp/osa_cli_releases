import osa_cli_releases.releasing as releasing
from prettytable import PrettyTable
from ruamel.yaml import YAML


def test_parse_requirements():
    req = list(releasing.parse_requirements("pip==18.0"))[0]
    assert req.name == "pip"
    assert req.specs == [("==", "18.0")]
    assert req.extras == []


# TODO(evrardjp): Implement mock on pypi API
def test_get_pypi_versions():
    pass


# TODO(evrardjp): Implement mock on pypi API
def test_get_pypi_version():
    pass


# TODO(evrardjp): Implement mock on pypi API
def test_parse_upper_constraints():
    pass


def test_discover_requirements_sha():
    assert (
        "4425ce22fda513fb7a20e77f28685004296731d0"
        == releasing.discover_requirements_sha(
            path="tests/fixtures/openstack_services.yml"
        )
    )


def test_print_requirements_state_not_in_uc(capsys):
    pins = {"pip": [("==", "18.0")]}
    latest_versions = {"pip": "18.0"}
    constraints_versions = {}
    releasing.print_requirements_state(pins, latest_versions, constraints_versions)
    out, err = capsys.readouterr()

    reftable = PrettyTable(
        ["Package", "Current Version Spec", "Latest version on PyPI", "Constrained to"]
    )
    reftable.add_row(["pip", "== 18.0", "18.0", "None"])
    print(reftable)
    out2, err2 = capsys.readouterr()
    assert out == out2
    assert err == err2
    assert err == ""


def test_print_requirements_state_in_uc(capsys):
    pins = {"pip": [("==", "18.0")]}
    latest_versions = {"pip": "18.0"}
    constraints_versions = {"pip": [("==", "30.3.0")]}
    releasing.print_requirements_state(pins, latest_versions, constraints_versions)
    out, err = capsys.readouterr()

    reftable = PrettyTable(
        ["Package", "Current Version Spec", "Latest version on PyPI", "Constrained to"]
    )
    reftable.add_row(["pip", "== 18.0", "18.0", "[('==', '30.3.0')]"])
    print(reftable)
    out2, err2 = capsys.readouterr()
    assert out == out2
    assert err == err2
    assert err == ""


def test_bump_upstream_repos_shas():
    pass


def test_find_yaml_files():
    assert len(releasing.find_yaml_files("tests/fixtures/*.txtttt")) == 0
    assert len(releasing.find_yaml_files("tests/fixturesy")) == 0
    assert len(releasing.find_yaml_files("tests/fixturesy/")) == 0
    assert len(releasing.find_yaml_files("tests/fixtures/")) == 2


def test_bump_upstream_repo_sha_file():
    pass


# def test_parse_repos_infos():
#    path = 'tests/fixtures/openstack_services.yml'
#    oss = releasing.parse_repos_info(path)
#    assert oss['requirements_git_repo'] == 'https://git.openstack.org/openstack/requirements'
#    assert oss['requirements_git_install_branch'] == '4425ce22fda513fb7a20e77f28685004296731d0'
#    assert oss['octavia_dashboard_git_project_group'] == 'horizon_all'


def test_build_repos_dict():
    yaml = YAML()
    with open("tests/fixtures/gnocchi.yml", "r") as fd:
        repofiledata = yaml.load(fd)
    repos = releasing.build_repos_dict(repofiledata)
    assert repos["gnocchi"]["url"] == "https://github.com/gnocchixyz/gnocchi"
    assert repos["gnocchi"]["sha"] == "711e51f706dcc5bc97ad14ddc8108e501befee23"
    assert repos["gnocchi"]["trackbranch"] == "stable/4.3"


def test_get_sha_from_ref():
    sha = releasing.get_sha_from_ref(
        "https://github.com/openstack/openstack-ansible.git", "newton-eol"
    )
    assert sha == "bf565c6ae34bb4343b4d6b486bd9b514de370b0a"
