import click
import osa_cli_releases.releasing as releasing


@click.group()
def releases():
    """ Tools for releasing OSA """
    pass

@releases.command('check_pins')
@click.pass_obj
@click.option('--requirements-sha',help="Sha used for fetching the upper constraints file in requirements")
@click.option('--file', 
              type=click.File(),
              help="path to global requirements pin file", default="global-requirement-pins.txt",)
def analyse_global_requirement_pins(global_ctx, **kwargs):
    """ Check a package list file for updates on PyPI or in upper constraints
    """
    debug = global_ctx['debug']
    pins = {
        pin.name: pin.specs
        for pin in releasing.parse_requirements(kwargs['file'])
    }
    if debug:
        print(pins)

    latest_versions = releasing.get_pypi_versions(pins.keys())

    if not kwargs['requirements_sha']:
        sha = releasing.discover_requirements_sha()
    else:
        sha = kwargs['requirements_sha']

    constraints_versions = {
        pin.name: pin.specs for pin in releasing.parse_upper_constraints(sha)
    }
    releasing.print_requirements_state(pins, latest_versions, constraints_versions)


@releases.command('bump_upstream_shas')
@click.pass_obj
@click.option('--path', 
              type=click.Path(
                  file_okay=False,
                  dir_okay=True,
                  writable=True,
                  resolve_path=True,
              ),
              help="path to the folder containing YAML files to update with new SHAs",
              default="playbooks/defaults/repo_packages/",)
def bump_upstream_repos_shas(global_ctx, **kwargs):
    """ Bump upstream projects SHAs.
    :param path: String containing the path of the YAML files formatted for updates
    """
    releasing.bump_upstream_repos_shas(kwargs['path'])


@releases.command('bump_roles')
@click.pass_obj
@click.option('--file', 
              type=click.File(),
              help="path to ansible-role-requirements.yml",
              default="ansible-role-requirements.yml",)
@click.argument('os-branch')
def bump_arr(global_ctx, **kwargs):
    """ Bump roles SHA and copies their releases notes.
    Also bumps roles from external sources when the branch to bump is master.
    """
    releasing.update_ansible_role_requirements_file(filename=args['file'],branchname=args['os-branch'])

@releases.command('bump_release_number')
@click.option('--release_type',type=click.Choice(choices=["bugfix", "feature", "milestone", "rc"]),
        help="The type of release to generate",
        default="bugfix")
@click.pass_obj
def bump_oa_release_number(global_ctx, **kwargs):
    """ Updates the version of the release in tree
    """
    debug = global_ctx['debug']

    current_version, filename = releasing.find_release_number()
    if debug:
        print("Found version %s in %s" % (current_version, filename))
    next_version = releasing.next_release_number(current_version, kwargs['release_type'])
    if debug:
        print("Updating %s to %s" % (filename, next_version))
    releasing.update_release_number(filename, ".".join(next_version))