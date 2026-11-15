"""Exact replay of finite transfer-matrix defect inequalities."""

from fractions import Fraction


DEFECT_SEED = 13_510_000
PRESSURE_SEED = 26_880_000


def defect_ratio(excited):
    return (1 + sum(excited)) ** 2 / (1 + sum(x*x for x in excited))


def verify_thermal_batch(batch):
    """Check the sharp doubling inequality and the seed conversion on rational inputs."""
    u = Fraction(40 ** 3, DEFECT_SEED)
    if (1 + u / (1 - u) ** 2) / (2 * DEFECT_SEED) > Fraction(1, PRESSURE_SEED):
        raise ValueError("The defect seed does not imply the pressure seed")
    x = Fraction(batch + 1, batch + 17)
    if defect_ratio((x*x,)) - 1 != doubling_bound(defect_ratio((x,)) - 1):
        raise ValueError("The one-excitation spectrum failed to attain the sharp bound")
    for n in range(1, 7):
        excited = tuple(Fraction(j, (n + 1) ** 2 + batch) for j in range(1, n + 1))
        a = defect_ratio(excited) - 1
        next_defect = defect_ratio(tuple(x*x for x in excited)) - 1
        if not 0 < a < 1 or next_defect > doubling_bound(a):
            raise ValueError("The exact doubling inequality failed on a finite spectrum")


def doubling_bound(a):
    return a*a / (2 - a*a)
