"""Curated mathematical routes and source references for ann missions."""

import copy

STRATEGIES = {}

def route(key, name, role, method, capability="research plan"):
    STRATEGIES[key] = dict(id=key, name=name, role=role, method=method, capability=capability)

route("exact", "Exact certificate", "verifier", "Derive a rational identity or compute an exact Sturm chain. Compare every coefficient and check the original domain.", "executable")
route("modular", "Modular obstruction", "refuter", "Reduce the original integer polynomial modulo a bounded list of moduli. An exhausted residue space with no zero rules out integer solutions.", "executable")
route("counterexample", "Counterexample search", "refuter", "Find a witness inside the stated domain. A positive finite search leaves the infinite claim open.", "executable on supported polynomial tasks")
route("formalization", "Formalization", "verifier", "Specify the theorem and hypotheses in Lean. Audit imports, statement equivalence, and axioms. Keep any unformalized premise visible.")
route("critique", "Independent critique", "critic", "Identify the first unsupported inference. Test quantifiers, boundary cases, and any interchange of limits.")
route("reduction", "Structural reduction", "researcher", "Reduce to a precise lemma and prove both directions if claiming equivalence. Name a concrete witness or obstruction.")
route("literature", "Source comparison", "researcher", "Compare the mission's registered references and optional pinned eBLLM route catalogue. Record assumptions and the exact scope of each result.")
route("ym-thermal", "Thermal defect", "researcher", "Convert the same-coupling time-doubling defect into a pressure seed. Check sharp same-box contraction and isolate the missing uniform initial estimate.", "executable on exact finite spectra")
route("ym-rg", "Renormalization group", "researcher", "Organize the blocked action by scale and bound the time-doubling defect of the remainder. Include large-field sectors and non-divisible box sizes.")
route("ym-spectrum", "Spectral counting", "researcher", "Separate the neutral and charged sectors. Obtain a physical gap lower bound and uniform control of low-lying multiplicities. An individual correlator cannot count all states.")
route("ym-os", "Continuum reconstruction", "critic", "Match the Wilson family, couplings, and denominator in the external construction. Check reflection, phase averaging, density of the observable core, and nontriviality.")
route("hodge-cycles", "Cycle construction", "researcher", "Construct cycles and compute their classes in a fixed rational basis. Recheck the span of divisor products on small powers of the elliptic curve with period i.", "executable on the elliptic-curve example")
route("hodge-periods", "Periods and monodromy", "researcher", "Use residues, Picard–Fuchs equations or monodromy to isolate candidate classes. Distinguish an exact rational relation from numerical period agreement.")
route("hodge-spread", "Families and specialization", "critic", "Check degree growth for the extra CM divisor direction as the order discriminant varies. Isolate the need to bound representatives of a fixed persistent class.", "executable on CM degree bounds")
route("hodge-blocks", "Mixed CM cycle construction", "researcher", "Separate imaginary quadratic field blocks. Multiply explicit coordinate and same-block divisor classes and check the rational invariant ranks.", "executable on CM products of dimension at most five")
route("hodge-normal", "Normal functions", "researcher", "Find an admissible normal function with the required singularity. Identify the exact implication to algebraicity and its hypotheses.")
route("rh-analytic", "Analytic and spectral criteria", "researcher", "Compare an explicit-formula positivity route with a reciprocal approximation route. Retain the full infinite quantifier and every boundary-limit estimate.")
route("d4-geometry", "Geometric certificates", "researcher", "Split contact and radial-shell cases. Check containment, exact volume and compatibility with unrestricted off-grid configurations.")
route("exact-sturm", "Sturm sign analysis", "verifier", "Check global univariate signs by an exact Sturm chain.", "executable on supported univariate tasks")
route("assumption-audit", "Assumption stress test", "critic", "Drop one proposed auxiliary hypothesis at a time. Construct a boundary case or a countermodel that isolates the hypothesis actually needed.")
route("limit-audit", "Quantifier and limit audit", "critic", "Place all scales and parameters in dependency order. Determine which constants must be uniform and give a sequence that exposes a nonuniform bound.")
route("construction", "Alternative construction", "researcher", "Start from a concrete example. State the invariant it satisfies and identify a construction that preserves it under the required extension.")

BASE = ["reduction", "critique", "formalization", "literature"]
WIDE = ["assumption-audit", "limit-audit", "construction"]

TARGETS = {
    "yang-mills": {
        "title": "Yang–Mills existence and mass gap",
        "statement": "Construct nontrivial quantum Yang–Mills theory on R⁴ for every compact simple gauge group and prove a strictly positive mass gap.",
        "strategies": ["ym-thermal", "ym-rg", "ym-spectrum", "ym-os"] + BASE,
        "gaps": ["Prove the same-coupling weak-coupling thermal-defect bound on the full rectangular window.",
                 "Match the continuum construction and finite-cutoff transfer estimates on one family.",
                 "Control neutral states and all required gauge groups."],
        "sources": [
            ["Jaffe and Witten, official problem", "https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf"],
            ["4Y-M proof progress", "https://github.com/anaxia-research/4Y-M/tree/4cfb040e4077a22f743da3a1abd2d23cc5dd277b/research/2026-11-15"],
            ["Sharp finite-transfer defect bounds", "https://github.com/anaxia-research/anaxia/blob/main/docs/ANN-YANG-MILLS-DEFECT.md"],
            ["November 2026 construction assessment", "https://alexisdpc.github.io/yang-mills/references/assessment-1-2026-11-10.pdf"]],
    },
    "hodge": {
        "title": "Rational Hodge conjecture",
        "statement": "For every smooth complex projective variety, prove that rational classes of type (p,p) are rational linear combinations of cycle classes of codimension p.",
        "strategies": ["hodge-cycles", "hodge-blocks", "hodge-periods", "hodge-spread", "hodge-normal"] + BASE,
        "gaps": ["Produce algebraic cycles for a general rational Hodge class in higher codimension.",
                 "Discharge the bounded-family hypothesis in the spreading route or find a replacement.",
                 "Prove class equality and track rational coefficients."],
        "sources": [
            ["Clay problem and Deligne description", "https://www.claymath.org/millennium/hodge-conjecture/"],
            ["Brosnan, Pearlstein and Schnell, normal functions", "https://arxiv.org/abs/0903.4903"],
            ["Toric differential forms and periods", "https://arxiv.org/abs/2306.12931"],
            ["Explicit elliptic power calculation", "https://github.com/anaxia-research/anaxia/blob/main/docs/ANN-HODGE-ELLIPTIC.md"],
            ["Mixed CM cycles and degree obstruction", "https://github.com/anaxia-research/anaxia/blob/main/docs/ANN-HODGE-CM-PRODUCTS.md"],
            ["Imai, On the Hodge groups of some abelian varieties", "https://www.jstage.jst.go.jp/article/kodaimath1949/27/3/27_3_367/_article/-char/en"],
            ["Rosen and Shnidman, Neron-Severi groups of product abelian surfaces", "https://arxiv.org/abs/1402.2233"],
            ["anaxia degree obstruction", "https://github.com/anaxia-research/anaxia/blob/main/docs/HODGE-DEGREE-OBSTRUCTION.md"]],
    },
    "riemann": {
        "title": "Riemann hypothesis",
        "statement": "Prove every nontrivial zero of the Riemann zeta function has real part 1/2.",
        "strategies": ["rh-analytic"] + BASE,
        "gaps": ["Establish an infinite-domain positivity or convergence criterion with its complete error bounds."],
        "sources": [["Clay problem description", "https://www.claymath.org/millennium/riemann-hypothesis/"],
                    ["anaxia reciprocal coefficient bounds", "https://github.com/anaxia-research/anaxia/blob/main/docs/RH-RECIPROCAL-COEFFICIENTS.md"]],
    },
    "d4": {
        "title": "D₄ sphere packing",
        "statement": "Prove the D₄ lattice sphere packing has maximum density among all packings in four-dimensional Euclidean space.",
        "strategies": ["d4-geometry"] + BASE,
        "gaps": ["Extend grid and local contact bounds to arbitrary configurations and the global density upper bound."],
        "sources": [["anaxia grid bounds", "https://github.com/anaxia-research/anaxia/blob/main/docs/D4-GRID-PACKINGS.md"]],
    },
    "polynomial-demo": {
        "title": "Exact nonnegativity demonstration",
        "statement": "Prove x⁴ − 2x³ + 2x² − 2x + 1 is nonnegative for all real x.",
        "strategies": ["exact-sturm"], "gaps": [], "sources": [],
        "task": {"schema_version": 1, "kind": "polynomial_nonnegative", "variables": ["x"],
                 "domain": {"kind": "real"}, "polynomial": [
                    {"coefficient": c, "powers": [i]} for i, c in enumerate(["1","-2","2","-2","1"])]},
    },
    "modular-demo": {
        "title": "Modular obstruction demonstration",
        "statement": "Prove that x² + y² = 3 has no integer solution.",
        "strategies": ["modular"], "gaps": [], "sources": [],
        "task": {"schema_version": 1, "kind": "integer_polynomial_zero", "variables": ["x","y"],
                 "polynomial": [{"coefficient": c, "powers": p} for c,p in
                                [("1",[2,0]),("1",[0,2]),("-3",[0,0])]]},
    },
}

IMPORTS = [
    ("hyperresearch", "MIT", "Source provenance and audit reference"),
    ("openworker", "MIT", "Local provider and worker orchestration reference"),
    ("agency-agents", "MIT", "Specialist role reference"),
    ("claude-code-templates", "MIT", "Template catalogue reference"),
    ("agentic-ai-apis", "unverified", "Provider catalogue reference"),
    ("animate", "MIT", "Procedural canvas design reference"),
    ("kimi-k3-in-c", "Apache-2.0", "Optional inference source. Runtime and weights are separate."),
    ("colibri", "Apache-2.0", "Optional inference source. Runtime and weights are separate."),
    ("COG-second-brain", "MIT", "Independent review and Markdown graph reference"),
    ("open-second-brain", "MIT", "Obsidian vault format reference"),
    ("claude-second-brain", "MIT", "Markdown knowledge graph reference"),
    ("ai-memory", "MIT", "Persistent context reference"),
    ("gbrain", "MIT", "Evidence graph reference"),
    ("floorplan", "MIT", "Workspace visualization reference"),
    ("free-claude-code", "unverified", "Inventory only"),
    ("YM", "Apache-2.0", "Continuum construction assessment reference"),
    ("Nielsen-and-Semita-Riemann-Proof-in-Lean4", "unverified", "Submitted proof claim. Statement and axioms require review."),
]

def catalog():
    return {
        "targets": [dict(id=key, **{field: value[field] for field in ("title", "statement", "strategies")})
                    for key, value in TARGETS.items()],
        "strategies": list(STRATEGIES.values()),
        "integrations": [dict(name=name, license=license, status="reference", role=role,
                              url="https://github.com/anaxia-research/" + name)
                         for name, license, role in IMPORTS],
        "engines": [
            {"name": "anaxia exact lab", "status": "built in", "role": "SOS, Sturm, exact witnesses and modular obstructions"},
            {"name": "OpenGluon / eBLLM", "status": "optional pinned source", "role": "Construction route catalogue from the existing engines/anaxia checkout"},
            {"name": "Ollama, compatible servers, Claude, OpenAI, Kimi", "status": "explicit model mode", "role": "Public proposals through existing provider adapters"},
        ],
    }

def template(name):
    return copy.deepcopy(TARGETS.get(name, {}))
