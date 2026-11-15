"""Mathematical routes and independent evidence checks."""

import json
from functools import lru_cache
from pathlib import Path

from .. import lab, number_theory, providers, reasoning
from .hodge import cm_product_check, divisor_degree_threshold, power_check
from .strategies import STRATEGIES
from .thermal import (DEFECT_SEED, PRESSURE_SEED, free_oscillator_obstruction,
                      verify_block_trace, verify_rational_spectra, verify_seam_clusters,
                      verify_seam_endpoints, verify_thermal_batch)

ROOT = Path(__file__).resolve().parents[2]
ATLAS = ROOT / "engines" / "anaxia" / "src" / "ebllm" / "research" / "data" / "construction-atlas.json"
CM_EXAMPLES = (((1, 2), (2, 2)), ((2, 2), (3, 2), (6, 1)), ((3, 4),), ((7, 1), (11, 3)))
CM_DISCRIMINANTS = (-4, -23, -163, -4 * 1_000_003)


def formalize(task):
    if task is None:
        return None
    if isinstance(task, dict) and task.get("kind") == "integer_polynomial_zero":
        return number_theory.validate(task)
    checked = lab.validate_task(task)
    checked.pop("certificate", None)
    return checked


def recheck(task, report):
    if not task or not isinstance(report, dict):
        return None
    try:
        if task["kind"] == "integer_polynomial_zero":
            if number_theory.validate(report.get("task")) != task:
                return None
            result = number_theory.verify(report)
        else:
            if reasoning.statement_digest(report.get("task")) != reasoning.statement_digest(task):
                return None
            result = lab.verify_report(report)
    except (KeyError, TypeError, ValueError):
        return None
    return result if result["valid"] and result["status"] != "inconclusive" else None


@lru_cache(maxsize=16)
def read_routes(path, target):
    """Read optional OpenGluon/eBLLM catalogue data as evidence leads."""
    try:
        with path.open(encoding="utf-8") as stream:
            raw = stream.read(500_001)
        if len(raw) > 500_000:
            return ()
        routes = json.loads(raw)["routes"]
        needles = {"yang-mills": ["yang", "mills"], "hodge": ["hodge"],
                   "riemann": ["riemann"], "d4": ["packing", "d4"]}.get(target, [])
        if not needles or not isinstance(routes, list):
            return ()
        return tuple(json.dumps(row, ensure_ascii=False)[:700] for row in routes
                     if isinstance(row, dict) and any(n in json.dumps(row).lower() for n in needles))[:3]
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return ()


@lru_cache(maxsize=64)
def exact(encoded, modulus):
    task = json.loads(encoded)
    if task["kind"] == "integer_polynomial_zero":
        return number_theory.solve(task, max_modulus=modulus)
    return lab.solve_task(task)


@lru_cache(maxsize=12)
def spectral_example(samples):
    from fractions import Fraction
    from scripts.check_thermal_gap_identifiability import family

    nodes, base, weights, epsilon, moments = family(samples)
    if (not all(0 < node < Fraction(1, 2) for node in nodes)
            or epsilon <= 0 or any(weight < 0 for weight in weights)):
        raise ValueError("Invalid spectral example")
    for degree, moment in enumerate(moments):
        left = sum(base * node ** degree for node in nodes)
        right = sum(w * node ** degree for node, w in zip(nodes, weights)) + epsilon * moment
        if left != right:
            raise ValueError("Spectral moment mismatch")
    return (f"Rechecked {samples + 1} exact moment equalities for abstract gapped and gapless spectra.",
            "Finite correlator samples do not identify a gap. The construction concerns abstract positive measures.")


def execute(mission, agent):
    strategy = STRATEGIES[agent["strategy"]]
    task = mission.get("task")
    result = dict(strategy=strategy["id"], role=strategy["role"], status="unresolved",
                  summary=strategy["method"], scope="Research obligation", model_used=False)
    if strategy["id"] == "literature":
        leads = read_routes(ATLAS, mission["template_id"])
        result["finding"] = "Sources available in the mission record."
        if leads:
            result["finding"] += " eBLLM construction-atlas matches: " + " | ".join(leads)
    if strategy["id"] == "ym-spectrum":
        result["finding"], result["scope"] = spectral_example(agent["slot"] % 12 + 1)
        result["status"] = "checked_subresult"
    if strategy["id"] == "ym-thermal":
        verify_thermal_batch(agent["slot"] % 16)
        result.update(status="checked_subresult",
                      finding=f"Rechecked sharp same-box defect contraction a(2T) <= a(T)^2/(2-a(T)^2). A uniform defect seed V/({DEFECT_SEED} T^3) implies the conditional pressure seed V/({PRESSURE_SEED} T^3).",
                      scope="Finite transfer operators at fixed coupling. The uniform weak-coupling input remains open.")
    if strategy["id"] == "ym-seams":
        verify_seam_endpoints(agent["slot"] % 32)
        result.update(status="checked_subresult",
                      finding="An exact finite transfer calculation checks two equal and two opposite permutation endpoints. The Wilson identity reduces the defect to the integrated connected response across two separated seams.",
                      scope="The replay checks rational endpoint algebra. The cutoff-uniform Wilson covariance estimate remains open.")
    if strategy["id"] == "ym-gaussian":
        lower, seed = free_oscillator_obstruction()
        result.update(status="checked_subresult",
                      finding=f"An even-parity massless oscillator at spatial side 2T has a thermal defect above {lower}, whereas the required seed is {seed}.",
                      scope="Exact bound in a Gaussian control model. This tests importing ultraviolet estimates into a thermal-integral argument.")
    if strategy["id"] == "ym-seam-clusters":
        verify_seam_clusters(agent["slot"] % 32)
        result.update(status="checked_subresult",
                      finding="An exact ring replay isolates one winding activity. On the doubled Wilson graph, Möbius activities that depend on only one seam cancel from the mixed difference.",
                      scope="Connectivity and cancellation are exact. Uniform Wilson cluster summability and the terminal remainder still need bounds.")
    if strategy["id"] == "ym-block-entropy":
        verify_block_trace(agent["slot"] % 32)
        result.update(status="checked_subresult",
                      finding="The exact transfer trace equals one plus the two-layer chi-square divergence. A conditional chain with tilted block histories replays that trace.",
                      scope="Abstract positive transfer operators. Uniform conditional block decorrelation remains an input for the Wilson family.")
    if strategy["id"] == "ym-spectrum-exhaustive":
        denominator = 4 + agent["slot"] % 32
        searched, qualifying, equalities = verify_rational_spectra(denominator)
        result.update(status="checked_subresult",
                      finding=f"Denominator {denominator}: exhausted {searched} spectra, with {qualifying} in the small-defect range and {equalities} attaining the bound.",
                      scope="Up to four positive excited weights on one rational grid. This is a finite transfer-bound check.",
                      searched=searched, qualifying=qualifying, equalities=equalities)
    if strategy["id"] == "hodge-cycles":
        power = agent["slot"] // len(mission["strategies"]) % 4 + 1
        ranks = power_check(power)
        result.update(status="checked_subresult",
                      finding=f"On E^{power} with E = C/(Z + iZ), rational divisor products have ranks {ranks} in codimensions 1 through {power}.",
                      scope="Exact exterior algebra for this fixed complex multiplication elliptic curve.")
    if strategy["id"] == "hodge-blocks":
        blocks = CM_EXAMPLES[agent["slot"] // len(mission["strategies"]) % len(CM_EXAMPLES)]
        ranks = cm_product_check(blocks)
        result.update(status="checked_subresult",
                      finding=f"Exact divisor-product ranks {ranks} for CM blocks (positive radical, multiplicity) {blocks}.",
                      scope="Products of CM elliptic curves, separated by distinct imaginary quadratic fields.")
    if strategy["id"] == "hodge-spread":
        delta = CM_DISCRIMINANTS[agent["slot"] // len(mission["strategies"]) % len(CM_DISCRIMINANTS)]
        degree = divisor_degree_threshold(delta)
        result.update(status="checked_subresult",
                      finding=f"At CM order discriminant {delta}, the least effective divisor degree seeing the non-real direction on E x E is {degree}.",
                      scope="Cutoff for spanning all divisor classes on E x E. The extra CM directions need not be persistent across the family.")
    if task and strategy["id"] in {"exact", "exact-sturm", "modular", "counterexample"}:
        report = exact(json.dumps(task, sort_keys=True), 4 + agent["slot"] % 13)
        verification = recheck(task, report)
        if verification:
            result.update(status=verification["status"], report=report,
                          summary=verification["reason"], scope=report["scope"])
            return result
    if agent["use_model"]:
        options = dict(mission["modelconfig"])
        model = options.pop("model")
        purpose = "certificate" if task and task["kind"] == "polynomial_nonnegative" else (
            "critique" if strategy["role"] == "critic" else "proposal")
        request = {"statement": mission["statement"], "original_task": task,
                   "public_research_method": strategy["method"], "open_gaps": mission["gaps"],
                   "replicate": agent["slot"], "references": mission["sources"]}
        if mission.get("brief"):
            request["research_brief"] = mission["brief"]
            request["expected_output"] = (
                "Give one concrete estimate and its derivation. State the first unproved premise and its scale "
                "dependence explicitly. Distinguish the assigned route from any earlier worker notes."
            )
        if result.get("finding"):
            request["existing_evidence"] = result["finding"]
        if agent.get("prior_findings"):
            request["prior_worker_notes_for_review"] = agent["prior_findings"]
        result["model_attempted"] = True
        try:
            response = providers.propose(request, model, purpose=purpose, **options)
            result["model_used"] = True
            text = response["proposal"]
            if purpose == "certificate":
                candidate = reasoning.extract_candidate(text)
                report = reasoning.verify_candidate(task, candidate)
                checked = recheck(task, report)
                if checked:
                    result.update(status=checked["status"], report=report,
                                  summary=checked["reason"], scope=report["scope"])
                result["finding"] = candidate["strategy"]
            elif result["status"] == "checked_subresult":
                result["proposal"] = text[:2400]
            else:
                result.update(status="unverified_proposal", finding=text[:2400])
        except ValueError as error:
            result["model_error"] = str(error)[:400]
    elif not task and "finding" not in result:
        result["finding"] = mission["gaps"][agent["slot"] % len(mission["gaps"])]
    return result
