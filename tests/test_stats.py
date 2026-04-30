import pytest

import driftmap_core


def test_module_exposes_phase1_functions():
    assert hasattr(driftmap_core, "ks_2samp")
    assert hasattr(driftmap_core, "mann_whitney")
    assert hasattr(driftmap_core, "cohen_d")


@pytest.mark.parametrize(
    "fn_name",
    ["ks_2samp", "mann_whitney", "cohen_d"],
)
def test_phase1_functions_exist(fn_name):
    assert callable(getattr(driftmap_core, fn_name))
