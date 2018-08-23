def test_import():
    import osa_cli_releases.releasing #noqa: F401
    import osa_cli_releases.cli #noqa: F401


def test_import_when_click():
    try:
        import click #noqa: F401
    except ImportError:
        pass
    else:
        import osa_cli_releases.click #noqa: F401
