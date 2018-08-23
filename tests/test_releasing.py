import osa_cli_releases.releasing as releasing
from prettytable import PrettyTable


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
        == releasing.discover_requirements_sha(path="tests/fixtures/openstack_services.yml")
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
    pass 
