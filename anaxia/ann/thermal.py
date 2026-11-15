"""Exact replay of finite transfer-matrix defect inequalities."""

from fractions import Fraction
from functools import lru_cache
from itertools import combinations_with_replacement, product


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


@lru_cache(maxsize=32)
def verify_seam_endpoints(batch):
    """Replay the four twist endpoint identities with exact positive matrices."""
    a = ((Fraction(2, 7), Fraction(1, batch + 9)), (Fraction(1, 9), Fraction(3, 8)))
    b = ((Fraction(5, 7), Fraction(1, 6)), (Fraction(1, batch + 10), Fraction(4, 9)))
    transfer = [[sum(a[x][y] * b[y][z] for y in range(2)) for z in range(2)] for x in range(2)]
    straight = sum(transfer[i][i] for i in range(2)) ** 2
    doubled = sum(transfer[i][j] * transfer[j][i] for i, j in product(range(2), repeat=2))
    for u, v in product(range(2), repeat=2):
        trace = sum(a[x0][ys[u]] * a[x1][ys[1-u]] * b[y0][xs[v]] * b[y1][xs[1-v]]
                    for x0, x1, y0, y1 in product(range(2), repeat=4)
                    for xs, ys in [((x0, x1), (y0, y1))])
        if trace != (straight if u == v else doubled):
            raise ValueError("Twisted replica endpoint trace mismatch")


def free_oscillator_obstruction():
    # On side 2T, the even excitation has weight q >= exp(-2*pi) > 3**-7.
    # Its defect is log((1+q)/(1-q)) >= 2*q.
    lower = Fraction(2, 3 ** 7)
    seed = Fraction(8, DEFECT_SEED)
    if lower <= seed:
        raise ValueError("The massless oscillator does not exceed the seed target")
    return lower, seed


@lru_cache(maxsize=32)
def verify_block_trace(batch):
    """Check the conditional chi-square chain on a positive four-state transfer."""
    q = Fraction(1, batch + 8)
    row = (1 - 7*q/2, q, 2*q, q/2)
    kernel = [[row[x ^ y] for y in range(4)] for x in range(4)]
    power = kernel
    for _ in range(batch % 4):
        power = [[sum(power[x][z] * kernel[z][y] for z in range(4))
                  for y in range(4)] for x in range(4)]
    trace = sum(power[x][y] * power[y][x] for x, y in product(range(4), repeat=2))
    tilted_mass = sum_of_increments = 0
    for law in power:
        for start in (0, 2):
            pair = law[start:start+2]
            mass = sum(pair)
            left_weight = mass**2 / 2
            chi2 = 2 * sum(p*p for p in pair) / mass**2 - 1
            tilted_mass += left_weight
            sum_of_increments += left_weight * chi2
    if tilted_mass + sum_of_increments != trace:
        raise ValueError("Conditional trace chain did not match the transfer trace")


@lru_cache(maxsize=32)
def verify_seam_clusters(batch):
    """Check exact localization of a winding interaction in a four-edge ring."""
    states = tuple(product((-1, 1), repeat=4))
    full = frozenset(range(4))
    for u, v in product(range(2), repeat=2):
        strength = (Fraction(u+1, batch+7), Fraction(1, 3), Fraction(v+1, 5), Fraction(1, 4))
        partitions = {}
        for mask in range(16):
            edges = frozenset(i for i in full if mask & (1 << i))
            mass = 0
            for state in states:
                weight = Fraction(1, len(states))
                for i in edges:
                    weight *= 1 + strength[i] * state[i] * state[(i+1) % 4]
                mass += weight
            partitions[edges] = mass
        for edges, mass in partitions.items():
            activity = mass
            for sub, value in partitions.items():
                if sub < edges and (len(edges) - len(sub)) % 2:
                    activity /= value
                elif sub < edges:
                    activity *= value
            if activity != (partitions[full] if edges == full else 1):
                raise ValueError("The nonwinding Möbius activity failed to cancel")


@lru_cache(maxsize=32)
def verify_rational_spectra(denominator):
    """Exhaust all grids of up to four positive excited weights."""
    if not 4 <= denominator <= 35:
        raise ValueError("Spectrum denominator must be between four and 35")
    searched = qualifying = equalities = 0
    q = denominator
    for count in range(1, 5):
        for weights in combinations_with_replacement(range(1, q), count):
            searched += 1
            d = sum(weights)
            e = sum(x*x for x in weights)
            base = q*q + e
            defect = (q + d) ** 2 - base
            if defect >= base:
                continue
            qualifying += 1
            base2 = q**4 + sum(x**4 for x in weights)
            observed = (base**2 - base2) * (2*base**2 - defect**2)
            bound = base2 * defect**2
            if observed > bound:
                raise ValueError("A rational spectrum violated the contraction")
            equalities += observed == bound
    return searched, qualifying, equalities
