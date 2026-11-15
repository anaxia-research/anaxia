"""Assemble reviewable paper and Obsidian bundles from recorded research."""

import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
import zipfile
from pathlib import Path
from uuid import uuid4

from .strategies import STRATEGIES
from .workers import recheck

ALLOWED = {"paper.md", "main.tex", "main.pdf", "evidence.json", "mission.zip"}
REFUTED = {"exact_univariate_refuted", "counterexample_verified"}
PROOF_TEXT = {
    "exact_sos_verified": "The attached rational sum of squares expands to the submitted polynomial. Each squared factor has nonnegative weight, so the polynomial is nonnegative on its stated real domain.",
    "exact_univariate_verified": "The exact sign algorithm checks the constant or leading sign and counts real roots of odd multiplicity using Sturm's theorem. Matching positive outer signs and absence of sign-changing roots certify nonnegativity on the real line.",
    "exact_univariate_refuted": "The exact sign algorithm finds a negative outer sign or an odd-multiplicity real root. In either case the polynomial takes a negative value on the real line.",
    "counterexample_verified": "Direct rational evaluation at the included witness is strictly negative. The verifier checks that the point belongs to the submitted domain.",
    "bounded_verified": "The verifier independently evaluates every point in the submitted finite integer box. The result covers that box.",
    "modular_obstruction_verified": "Every integer solution would reduce to a residue vector modulo the reported modulus. Exact enumeration finds no residue vector at which the polynomial is zero, excluding every integer solution.",
}


def markdown(value):
    raw = "".join(" " if ord(c) < 32 else c for c in str(value))
    return re.sub(r"([\\\x60*_{}\[\]<>#|!&])", r"\\\1", raw)


def latex(value):
    equivalents = str.maketrans({"²": "^2", "³": "^3", "⁴": "^4", "₄": "_4", "–": "-",
                                  "—": "-", "−": "-", "→": "->", "≤": "<=", "≥": ">=",
                                  "χ": "chi", "β": "beta", "ε": "epsilon", "ℓ": "ell"})
    ascii_text = unicodedata.normalize("NFKD", str(value).translate(equivalents))
    ascii_text = "".join(c if c.isascii() and ord(c) >= 32 else " " for c in ascii_text
                         if not unicodedata.combining(c))
    escape = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "%": r"\%", "&": r"\&",
              "$": r"\$", "#": r"\#", "_": r"\_", "^": r"\textasciicircum{}",
              "~": r"\textasciitilde{}", "<": r"\textless{}", ">": r"\textgreater{}"}
    return "".join(escape.get(c, c) for c in ascii_text)


def checked_evidence(mission, records):
    unique = {}
    for record in records:
        report = record.get("report")
        if not isinstance(report, dict):
            continue
        # Strategy, author, and model metadata do not affect the canonical check.
        body = json.dumps(report, sort_keys=True, ensure_ascii=True)
        key = hashlib.sha256(body.encode()).hexdigest()
        if key not in unique:
            verdict = recheck(mission.get("task"), report)
            if verdict:
                unique[key] = report
    return list(unique.values())


def research_summary(mission, records):
    verified = checked_evidence(mission, records)
    signs = {report["status"] in REFUTED for report in verified}
    conclusion = ("conflicting evidence requiring review" if len(signs) == 2 else
                  "formal task refuted" if signs == {True} else
                  "formal task verified" if signs else "unresolved")
    per_route = {}
    for record in records:
        key = record.get("strategy")
        if not isinstance(key, str) or key not in STRATEGIES:
            continue
        group = per_route.setdefault(key, {"count": 0, "examples": [], "model_notes": [], "model_errors": 0})
        group["count"] += 1
        group["model_errors"] += bool(record.get("model_error"))
        text = record.get("finding")
        proposal = record.get("proposal")
        if record.get("status") == "unverified_proposal":
            proposal, text = text, None
        if isinstance(proposal, str) and proposal[:2000] not in group["model_notes"] and len(group["model_notes"]) < 2:
            group["model_notes"].append(proposal[:2000])
        for metric in ("searched", "qualifying", "equalities"):
            if metric in record:
                counts = group.setdefault("replay_counts", {})
                counts[metric] = counts.get(metric, 0) + record[metric]
        limit = 4 if key in {"hodge-cycles", "hodge-blocks", "hodge-spread"} else 2
        if isinstance(text, str) and text not in group["examples"] and len(group["examples"]) < limit:
            group["examples"].append(text[:1200])
    return conclusion, verified, per_route


def polynomial_text(task):
    terms = []
    for term in task["polynomial"]:
        monomial = " ".join(f"{var}^{power}" if power > 1 else var
                            for var, power in zip(task["variables"], term["powers"]) if power)
        terms.append(f"({term['coefficient']})" + (f" {monomial}" if monomial else ""))
    expression = " + ".join(terms) or "0"
    if task["kind"] == "integer_polynomial_zero":
        return f"No integer assignment makes {expression} equal to zero."
    bounds = task["domain"]
    return f"{expression} is nonnegative on the submitted domain {json.dumps(bounds, ensure_ascii=True)}."


def export(mission, records, directory, *, pdf=False):
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / uuid4().hex
    output.mkdir()
    conclusion, verified, per_route = research_summary(mission, records)
    sections = [
        ("Research question", [mission["statement"]]),
        ("Evidence and scope", [f"Run status is {mission['status']}. The evidence conclusion is {conclusion}.",
                                f"The run recorded {len(records):,} worker outcomes."]),
    ]
    if mission.get("brief"):
        sections[0][1].append(mission["brief"])
    if mission.get("task"):
        sections[1][1].append("Exact claim checked: " + polynomial_text(mission["task"]))
    if errors := sum(route["model_errors"] for route in per_route.values()):
        sections[1][1].append(f"{errors} model requests or proposal checks returned errors. See the evidence file for counts by route.")
    if verified:
        sections.append(("Verification argument", [
            PROOF_TEXT[status] for status in sorted({report["status"] for report in verified})
        ] + ["The attached evidence file contains the independently rechecked certificate data."]))
    else:
        sections.append(("Open proof obligations", mission["gaps"]))
    path = output / "vault"
    path.mkdir()
    route_notes = []
    for key, stats in per_route.items():
        strategy = STRATEGIES[key]
        route_notes.append("[[" + key + "]]")
        sections.append((strategy["name"], [strategy["method"], f"Recorded attempts: {stats['count']}."]
                         + stats["examples"]
                         + (["Model proposals awaiting review."] + stats["model_notes"] if stats["model_notes"] else [])))
        note = [f"# {markdown(strategy['name'])}", "", "[[mission]]", "",
                markdown(strategy["method"]), "", *map(markdown, stats["examples"])]
        if stats["model_notes"]:
            note.extend(["", "## Unverified model proposals", *map(markdown, stats["model_notes"])])
        (path / f"{key}.md").write_text("\n".join(note) + "\n", encoding="utf-8")
    sources = [f"{name}. {url}" for name, url in mission["sources"]]
    if sources:
        sections.append(("Registered references", sources))
    if any(record.get("model_used") for record in records):
        disclosure = "Optional model services assisted with research proposals. Review and disclosure remain the author's responsibility."
    elif any(record.get("model_attempted") for record in records):
        disclosure = "Model calls were attempted and no model output was used. This generated draft requires author review."
    else:
        disclosure = "The run used deterministic software. This generated draft requires author review."
    sections.append(("Declarations", [disclosure, "Funding and conflicts of interest require author confirmation.",
                                     "Evidence and replay commands accompany the draft."]))
    paper = [f"# {markdown(mission['title'])}", "", f"**Prepared for {markdown(mission['author'])}**",
             "", f"Mission {mission['id']}", ""]
    tex = [r"\documentclass[11pt]{article}", r"\usepackage[T1]{fontenc}", r"\usepackage{lmodern}",
           r"\usepackage[margin=28mm]{geometry}", r"\usepackage{xurl}", r"\usepackage[hidelinks]{hyperref}",
           r"\setlength{\emergencystretch}{2em}", r"\title{" + latex(mission["title"]) + "}",
           r"\author{" + latex(mission["author"]) + "}", r"\date{}",
           r"\begin{document}", r"\maketitle", r"\noindent\textit{Research draft for review.}\par"]
    for title, paragraphs in sections:
        paper.extend([f"## {title}", "", *[markdown(p) + "\n" for p in paragraphs]])
        tex.append(r"\section*{" + latex(title) + "}")
        if title == "Registered references":
            tex.extend(latex(name) + r". \url{" + url + "}\n" for name, url in mission["sources"])
        else:
            tex.extend(latex(p) + "\n" for p in paragraphs)
    tex.append(r"\end{document}")
    (output / "paper.md").write_text("\n".join(paper) + "\n", encoding="utf-8")
    (output / "main.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    data = dict(schema_version=1, mission={key: value for key, value in mission.items() if key != "modelconfig"},
                conclusion=conclusion, checked_reports=verified, strategy_summaries=per_route,
                recorded_jobs=len(records))
    (output / "evidence.json").write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    vault = [f"# {markdown(mission['title'])}", "", markdown(mission["statement"]), "",
             f"Evidence conclusion: {conclusion}.", "", "## Research routes", *["- " + note for note in route_notes]]
    if sources:
        vault.extend(["", "## Registered sources", *["- " + markdown(source) for source in sources]])
    (path / "mission.md").write_text("\n".join(vault) + "\n", encoding="utf-8")
    built_pdf = False
    if pdf:
        engine = shutil.which("pdflatex")
        if not engine:
            raise ValueError("PDF export requires pdflatex on PATH. The LaTeX and Markdown files are saved.")
        env_args = [engine, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        try:
            run = subprocess.run(env_args, cwd=output, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 timeout=45, check=False)
        except subprocess.TimeoutExpired:
            raise ValueError("PDF compilation reached its time limit. The draft sources are saved.") from None
        if run.returncode != 0:
            raise ValueError("PDF compilation failed. The draft sources and TeX log are saved.")
        built_pdf = (output / "main.pdf").is_file()
    members = ["paper.md", "main.tex", "evidence.json"] + (["main.pdf"] if built_pdf else [])
    with zipfile.ZipFile(output / "mission.zip", "w", zipfile.ZIP_DEFLATED) as package:
        for name in members:
            package.write(output / name, name)
        for note in sorted(path.glob("*.md")):
            package.write(note, "vault/" + note.name)
    return {"directory": str(output), "files": members + ["mission.zip"], "status": conclusion}
