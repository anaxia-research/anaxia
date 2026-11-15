"""Exact exterior algebra for powers of the elliptic curve with period i."""

from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from math import comb


def wedge(left, right):
    result = {}
    for a, x in left.items():
        for b, y in right.items():
            if set(a).isdisjoint(b):
                product = tuple(sorted(a + b))
                sign = (-1) ** sum(i > j for i in a for j in b)
                result[product] = result.get(product, 0) + sign * x * y
    return {key: value for key, value in result.items() if value}


def rotation(poly):
    image = {}
    for form, coefficient in poly.items():
        for index, term in enumerate(form):
            changed = form[:index] + (term ^ 1,) + form[index + 1:]
            if len(set(changed)) != len(changed):
                continue
            key = tuple(sorted(changed))
            sign = (-1) ** (term % 2 + sum(a > b for a, b in combinations(changed, 2)))
            image[key] = image.get(key, 0) + coefficient * sign
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


@lru_cache(maxsize=4)
def power_check(n):
    if not 1 <= n <= 4:
        raise ValueError("This executable example supports powers 1 through 4")
    divisors = [{(2*i, 2*i+1): 1} for i in range(n)]
    for i, j in combinations(range(n), 2):
        a, b = 2*i, 2*j
        divisors.extend([{(a, b+1): 1, (a+1, b): -1},
                         {(a, b): 1, (a+1, b+1): 1}])
    basis = {(): {(): Fraction(1)}}
    ranks = []
    for p in range(1, n+1):
        products = {}
        for divisor in divisors:
            for form in basis.values():
                product = wedge(divisor, form)
                if rotation(product):
                    raise ValueError("Algebraic divisor product failed the Hodge type check")
                extend_basis(products, product)
        if len(products) != comb(n, p) ** 2:
            raise ValueError("Divisor products failed to span")
        ranks.append(len(products))
        basis = products
    return tuple(ranks)
