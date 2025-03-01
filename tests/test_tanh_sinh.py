import numpy as np
import pytest
import sympy
from mpmath import mp

import tanh_sinh

mp.dps = 50

test_cases = [
    (lambda _: 1, -1, +1, 2),
    (lambda _: 1, 0, +5, 5),
    (lambda t: t, -0, +1, sympy.Rational(1, 2)),
    (lambda t: t ** 2, -1, +1, sympy.Rational(2, 3)),
    # Bailey example 1:
    (lambda t: t * sympy.log(1 + t), 0, 1, sympy.Rational(1, 4)),
    # Bailey example 2:
    (lambda t: t ** 2 * sympy.atan(t), 0, 1, (sympy.pi - 2 + 2 * sympy.log(2)) / 12),
    # Bailey example 3:
    (
        lambda t: sympy.exp(t) * sympy.cos(t),
        0,
        mp.pi / 2,
        (sympy.exp(sympy.pi / 2) - 1) / 2,
    ),
    # Bailey example 4:
    (
        lambda t: sympy.atan(sympy.sqrt(2 + t ** 2))
        / (1 + t ** 2)
        / sympy.sqrt(2 + t ** 2),
        0,
        1,
        sympy.pi ** 2 * sympy.Rational(5, 96),
    ),
    # Bailey example 5:
    (lambda t: sympy.sqrt(t) * sympy.log(t), 0, 1, -sympy.Rational(4, 9)),
    # Bailey example 6 with singularity moved to 0.
    (lambda t: sympy.sqrt(2 * t - t ** 2), 0, 1, sympy.pi / 4),
    # Bailey example 8:
    (lambda t: sympy.log(t) ** 2, 0, 1, 2),
    # Bailey example 9:
    (lambda t: sympy.log(sympy.sin(t)), 0, mp.pi / 2, -mp.pi * mp.log(2) / 2),
    # Bailey example 11:
    (lambda s: 1 / (1 - 2 * s + 2 * s ** 2), 0, 1, mp.pi / 2),
    # Bailey example 13:
    (lambda s: sympy.exp(-((1 / s - 1) ** 2) / 2) / s ** 2, 0, 1, mp.sqrt(mp.pi / 2)),
    # Bailey example 14:
    (
        lambda s: sympy.exp(1 - 1 / s) * sympy.cos(1 / s - 1) / s ** 2,
        0,
        1,
        sympy.Rational(1, 2),
    ),
]


@pytest.mark.parametrize("f, a, b, exact", test_cases)
def test_tanh_sinh(f, a, b, exact):
    # test fine error estimate
    mp.dps = 50

    tol = 10 ** (-mp.dps)
    tol2 = 10 ** (-mp.dps + 1)

    t = sympy.Symbol("t")
    f_with_derivatives = (
        f,
        sympy.lambdify(t, sympy.diff(f(t), t, 1), modules=["mpmath"]),
        sympy.lambdify(t, sympy.diff(f(t), t, 2), modules=["mpmath"]),
    )

    value, _ = tanh_sinh.integrate(f_with_derivatives, a, b, tol, mode="mpmath")
    assert abs(value - exact) < tol2

    # test with crude estimate
    value, _ = tanh_sinh.integrate(f, a, b, tol, mode="mpmath")
    assert abs(value - exact) < tol2


@pytest.mark.parametrize("f, a, b, exact", test_cases)
def test_tanh_sinh_numpy(f, a, b, exact):
    # test fine error estimate
    tol = 1.0e-14
    tol2 = 1.0e-13

    t = sympy.Symbol("t")
    f_with_derivatives = (
        sympy.lambdify(t, f(t), modules=["numpy"]),
        sympy.lambdify(t, sympy.diff(f(t), t, 1), modules=["numpy"]),
        sympy.lambdify(t, sympy.diff(f(t), t, 2), modules=["numpy"]),
    )

    a = float(a)
    b = float(b)

    value, _ = tanh_sinh.integrate(f_with_derivatives, a, b, tol)
    assert abs(value - exact) < tol2

    # test with crude estimate
    f = sympy.lambdify(t, f(t), modules=["numpy"])
    value, _ = tanh_sinh.integrate(f, a, b, tol)
    assert abs(value - exact) < tol2


def test_tanh_sinh_numpy_example():
    tol = 1.0e-14
    val, _ = tanh_sinh.integrate(
        lambda x: np.exp(x) * np.cos(x),
        0,
        np.pi / 2,
        tol,
        # f_derivatives={
        #     1: lambda x: np.exp(x) * (np.cos(x) - np.sin(x)),
        #     2: lambda x: -2 * np.exp(x) * np.sin(x),
        # },
    )
    exact = (np.exp(np.pi / 2) - 1) / 2

    assert abs(val - exact) < tol


# Test functions with singularities at both ends.
@pytest.mark.parametrize(
    "f_left, f_right, b, exact",
    # Bailey example 7 (f only has one singularity, but derivatives have two):
    [
        (
            lambda t: sympy.sqrt((1 - t) / (2 * t - t ** 2)),
            lambda t: sympy.sqrt(t / (1 - t ** 2)),
            1,
            (
                2
                * sympy.sqrt(sympy.pi)
                * sympy.gamma(sympy.Rational(3, 4))
                / sympy.gamma(sympy.Rational(1, 4))
            ),
        )
    ]
    # Bailey example 10:
    # singularity on the right, derivative singularities at both ends
    + [
        (
            lambda t: sympy.sqrt(sympy.tan(t)),
            lambda t: 1 / sympy.sqrt(sympy.tan(t)),
            mp.pi / 2,
            mp.pi / mp.sqrt(2),
        )
    ]
    # Bailey example 12:
    + [
        (
            lambda s: sympy.exp(1 - 1 / s) / sympy.sqrt(s ** 3 - s ** 4),
            lambda s: sympy.exp(s / (s - 1))
            / sympy.sqrt(s * (s * ((3 - s) * s - 3) + 1)),
            1,
            mp.sqrt(mp.pi),
        )
    ],
)
def test_singularities_at_both_ends(f_left, f_right, b, exact):
    # test fine error estimate
    tol = 10 ** (-mp.dps)

    t = sympy.Symbol("t")
    fl = (
        f_left,
        sympy.lambdify(t, sympy.diff(f_left(t), t, 1), modules=["mpmath"]),
        sympy.lambdify(t, sympy.diff(f_left(t), t, 2), modules=["mpmath"]),
    )
    fr = (
        f_right,
        sympy.lambdify(t, sympy.diff(f_right(t), t, 1), modules=["mpmath"]),
        sympy.lambdify(t, sympy.diff(f_right(t), t, 2), modules=["mpmath"]),
    )

    value, _ = tanh_sinh.integrate_lr(fl, fr, b, tol, mode="mpmath")
    tol2 = 10 ** (-mp.dps + 1)
    assert abs(value - exact) < tol2

    # # test with crude estimate
    # fl = {0: f_left}
    # fr = {0: f_right}
    # value, _ = tanh_sinh.integrate_lr(fl, fr, b, tol)
    # tol2 = 10**(-mp.dps + 2)
    # assert abs(value - exact) < tol2


@pytest.mark.parametrize(
    "f, a, b, exact", [(lambda t: t ** 2, -1, +1, sympy.Rational(2, 3))]
)
def test_low_precision(f, a, b, exact):
    mp.dps = 10

    t = sympy.Symbol("t")
    f_with_derivatives = (
        f,
        sympy.lambdify(t, sympy.diff(f(t), t, 1), modules=["mpmath"]),
        sympy.lambdify(t, sympy.diff(f(t), t, 2), modules=["mpmath"]),
    )

    tol = 1.0e-2
    value, _ = tanh_sinh.integrate(f_with_derivatives, a, b, tol, mode="mpmath")
    assert abs(value - exact) < tol


if __name__ == "__main__":
    # test_tanh_sinh(
    #     lambda t: 1, 0, 1, 1
    #     )
    # test_singularities_at_both_ends(
    #     lambda s: sympy.exp(1 - 1 / s) / sympy.sqrt(s ** 3 - s ** 4),
    #     lambda s: sympy.exp(s / (s - 1)) / sympy.sqrt(s * (s * ((3 - s) * s - 3) + 1)),
    #     1,
    #     mp.sqrt(mp.pi),
    # )
    test_tanh_sinh_numpy_example()
