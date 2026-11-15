"""Exact cohomology of products of CM elliptic curves."""

from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from math import comb, isqrt


def wedge(left, right):
    result = {}
    for a, x in left.items():
        for b, y in right.items():
            if set(a).isdisjoint(b):
                product = tuple(sorted(a + b))
                sign = (-1) ** sum(i > j for i in a for j in b)
                result[product] = result.get(product, 0) + sign * x * y
    return {key: value for key, value in result.items() if value}


def rotation(poly, start, stop, d):
    image = {}
    for form, coefficient in poly.items():
        for index, term in enumerate(form):
            if not start <= term < stop:
                continue
            changed = form[:index] + (term ^ 1,) + form[index + 1:]
            if len(set(changed)) != len(changed):
                continue
            key = tuple(sorted(changed))
            sign = (-1) ** sum(a > b for a, b in combinations(changed, 2))
            image[key] = image.get(key, 0) + coefficient * sign * (-d if term % 2 else 1)
    return {key: value for key, value in image.items() if value}


def extend_basis(basis, poly):
    remaining = dict(poly)
    while remaining:
        pivot = min(remaining)
        coefficient = remaining[pivot]
        if pivot not in basis:
            basis[pivot] = {key: Fraction(value) / coefficient for key, value in remaining.items()}
            return
        for key, value in basis[pivot].items():
            reduced = remaining.get(key, 0) - coefficient * value
            if reduced:
                remaining[key] = reduced
            else:
                remaining.pop(key, None)


@lru_cache(maxsize=32)
def cm_product_check(blocks):
    if not blocks or any(d < 1 or n < 1 for d, n in blocks) or sum(n for _, n in blocks) > 5:
        raise ValueError("Supply positive blocks of total dimension at most five")
    if any(isqrt(d * e) ** 2 == d * e for (d, _), (e, _) in combinations(blocks, 2)):
        raise ValueError("Use one block per imaginary quadratic field")
    divisors, rotations = [], []
    expected, start = [1], 0
    for d, n in blocks:
        stop = start + 2 * n
        rotations.append((start, stop, d))
        axes = range(start, stop, 2)
        divisors.extend({(a, a+1): 1} for a in axes)
        for a, b in combinations(axes, 2):
            divisors.extend([{(a, b+1): 1, (a+1, b): -1},
                             {(a, b): d, (a+1, b+1): 1}])
        ranks = [0] * (len(expected) + n)
        for p, rank in enumerate(expected):
            for q in range(n + 1):
                ranks[p + q] += rank * comb(n, q) ** 2
        expected, start = ranks, stop
    basis = {(): {(): Fraction(1)}}
    ranks = []
    for target in expected[1:]:
        products = {}
        for divisor in divisors:
            for form in basis.values():
                product = wedge(divisor, form)
                if any(rotation(product, *block) for block in rotations):
                    raise ValueError("Algebraic divisor product failed the Hodge type check")
                extend_basis(products, product)
        if len(products) != target:
            raise ValueError("Divisor products failed to span")
        ranks.append(len(products))
        basis = products
    return tuple(ranks)


def power_check(n):
    return cm_product_check(((1, n),))


def divisor_degree_threshold(discriminant):
    """Check the least effective degree seeing the non-real off-diagonal direction."""
    size = -discriminant
    b = discriminant % 4
    if size < 3 or b not in (0, 1):
        raise ValueError("Expected a negative imaginary quadratic order discriminant")
    degree = isqrt(size - 1) + 1
    norm = (size + b) // 4
    a = degree // 2
    if a * (degree - a) < norm or (degree - 1) ** 2 >= size:
        raise ValueError("The optimal-degree construction failed its exact inequalities")
    return degree
