import opf


def test_pipeline_version():
    """Tripwire: bumping this rebuilds every family, so it must be deliberate.

    Update the number here in the same commit that bumps it, with the reason
    recorded in the comment next to PIPELINE_VERSION.
    """
    assert opf.PIPELINE_VERSION == 22
