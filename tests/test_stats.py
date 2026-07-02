import numpy as np
import pytest
from scipy.stats import ks_2samp, mannwhitneyu

import driftmap_core


RTOL = 1e-10
ATOL = 1e-12


def cohens_d_reference(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n1, n2 = a.size, b.size
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    dof = n1 + n2 - 2
    if dof <= 0:
        pooled_var = 0.0
    else:
        pooled_var = ((n1 - 1) * var_a + (n2 - 1) * var_b) / dof
    pooled_std = np.sqrt(pooled_var)
    mean_diff = np.mean(a) - np.mean(b)
    if pooled_std == 0.0:
        if mean_diff == 0.0:
            return 0.0
        raise ValueError("Cohen's d undefined when pooled std is zero")
    return mean_diff / pooled_std


@pytest.mark.parametrize(
    "fn_name",
    ["ks_2samp", "mann_whitney", "cohen_d"],
)
def test_phase1_functions_exist(fn_name):
    assert callable(getattr(driftmap_core, fn_name))


@pytest.mark.parametrize(
    "a,b",
    [
        ([1.0, 2.0, 3.0], [2.0, 3.0, 4.0, 5.0]),
        ([0.0], [1.0]),
        ([1.5, 2.5, 3.5, 4.5], [2.0, 2.0, 8.0]),
        (list(range(20)), [x * 0.7 + 3.0 for x in range(25)]),
    ],
)
def test_ks_2samp_matches_scipy_asymptotic(a, b):
    expected = ks_2samp(a, b, method="asymp").pvalue
    actual = driftmap_core.ks_2samp(a, b)
    assert actual == pytest.approx(expected, rel=RTOL, abs=ATOL)


@pytest.mark.parametrize(
    "a,b",
    [
        ([1.0, 2.0, 3.0], [2.0, 3.0, 4.0, 5.0]),
        ([0.0], [1.0]),
        ([1.0, 1.0, 2.0, 3.0], [2.0, 2.0, 2.0, 9.0]),
        (list(range(15)), [x + 0.25 for x in range(18)]),
    ],
)
def test_mann_whitney_matches_scipy(a, b):
    expected = mannwhitneyu(
        a, b, alternative="two-sided", use_continuity=True
    ).pvalue
    actual = driftmap_core.mann_whitney(a, b)
    assert actual == pytest.approx(expected, rel=RTOL, abs=ATOL)


@pytest.mark.parametrize(
    "a,b",
    [
        ([1.0, 2.0, 3.0], [2.0, 3.0, 4.0, 5.0]),
        ([10.0, 12.0, 14.0], [11.0, 13.0, 15.0, 17.0]),
        (list(range(30)), [x * 1.1 + 2.0 for x in range(28)]),
    ],
)
def test_cohen_d_matches_numpy_reference(a, b):
    expected = cohens_d_reference(a, b)
    actual = driftmap_core.cohen_d(a, b)
    assert actual == pytest.approx(expected, rel=RTOL, abs=ATOL)


def test_random_seeded_fixtures_match_references():
    rng = np.random.default_rng(42)
    a = rng.normal(loc=0.0, scale=1.0, size=80).tolist()
    b = rng.normal(loc=0.35, scale=1.1, size=95).tolist()

    assert driftmap_core.ks_2samp(a, b) == pytest.approx(
        ks_2samp(a, b, method="asymp").pvalue, rel=RTOL, abs=ATOL
    )
    assert driftmap_core.mann_whitney(a, b) == pytest.approx(
        mannwhitneyu(a, b, alternative="two-sided", use_continuity=True).pvalue,
        rel=RTOL,
        abs=ATOL,
    )
    assert driftmap_core.cohen_d(a, b) == pytest.approx(
        cohens_d_reference(a, b), rel=RTOL, abs=ATOL
    )


@pytest.mark.parametrize(
    "fn_name,empty_a,empty_b",
    [
        ("ks_2samp", [], [1.0]),
        ("ks_2samp", [1.0], []),
        ("mann_whitney", [], [1.0]),
        ("mann_whitney", [1.0], []),
        ("cohen_d", [], [1.0]),
        ("cohen_d", [1.0], []),
    ],
)
def test_empty_input_raises_value_error(fn_name, empty_a, empty_b):
    fn = getattr(driftmap_core, fn_name)
    with pytest.raises(ValueError, match="non-empty"):
        fn(empty_a, empty_b)


def test_cohen_d_zero_pooled_std_equal_means_returns_zero():
    assert driftmap_core.cohen_d([5.0, 5.0, 5.0], [5.0, 5.0]) == 0.0


def test_cohen_d_zero_pooled_std_unequal_means_raises():
    with pytest.raises(ValueError, match="undefined"):
        driftmap_core.cohen_d([1.0, 1.0], [2.0, 2.0])
