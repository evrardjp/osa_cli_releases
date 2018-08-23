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
    pass


def bump_arr():
    pass


def bump_oa_release_number():
    pass
