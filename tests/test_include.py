def test_import():
    import osa_cli_releases.releasing
    import osa_cli_releases.cli


def test_import_when_click():
    try:
        import click
    except ImportError:
        pass
    else:
        import osa_cli_releases.click
