"""Local prompt packaging and manual evaluation records. No model/network calls."""

import argparse
from collections import Counter
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import random
import re
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parent.parent
VERSIONS = ("0.2", "0.3")
CONDITIONS = ("B", "v0.2", "v0.3")
METRICS = (
    "critical_failure",
    "factual_or_reasoning_error",
    "wrong_agreement",
    "wrong_rejection",
    "missed_required_content",
    "unnecessary_qualification",
    "repeated_interruption",
    "missed_relevant_condition",
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path, records):
    Path(path).write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def digest(text):
    return sha256(text.encode("utf-8")).hexdigest()


def modules_for(version):
    if version not in VERSIONS:
        raise ValueError("Unknown prompt version")
    source = (ROOT / "prompts" / f"minimal-core-v{version}.md").read_text(encoding="utf-8-sig")
    blocks = re.findall(r"^## ([FJEW])：[^\n]*\n+```text\n(.*?)\n```", source, re.M | re.S)
    if [name for name, _ in blocks] != list("FJEW"):
        raise ValueError(f"Expected one F/J/E/W block in version {version}")
    return dict(blocks)


def prompt(version, selected="FJE"):
    if not selected or len(set(selected)) != len(selected) or any(m not in "FJEW" for m in selected):
        raise ValueError("Modules must be distinct letters from FJEW, in desired order")
    blocks = modules_for(version)
    return "\n\n".join(blocks[m] for m in selected)


def skill_text(version):
    return (
        "---\nname: dog-adhd\n"
        "description: 按 Dog-ADHD 偏好组织回答，在用户要求直接、自然、有依据且保留任务内容的协作方式时使用。\n"
        f'metadata:\n  source-version: "{version}"\n---\n\n'
        "# Dog-ADHD\n\n"
        + prompt(version)
        + "\n\n## 长文编辑时按需应用\n\n"
        + modules_for(version)["W"]
        + "\n"
    )


def build_skill(version, output, check=False):
    target = Path(output) / "SKILL.md"
    expected = skill_text(version)
    if check:
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            raise ValueError("Skill differs from source; run build-skill")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(expected, encoding="utf-8", newline="\n")
    return target


def validate_suite(suite):
    cases = suite.get("cases", [])
    if not suite.get("suite_id") or not cases:
        raise ValueError("Suite needs suite_id and cases")
    ids = set()
    for case in cases:
        case_id = case.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", case_id) or case_id in ids:
            raise ValueError("Case IDs must be distinct safe names")
        ids.add(case_id)
        if not case.get("scenario_id"):
            raise ValueError(f"Missing scenario_id: {case_id}")
        for field in ("user_turns", "criteria"):
            values = case.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
                raise ValueError(f"Missing/invalid {field}: {case_id}")
    return cases


def prepare(output, suite_path, conditions, repeats=1, selected="FJE"):
    if repeats < 1 or not conditions or len(set(conditions)) != len(conditions):
        raise ValueError("Use positive repeats and distinct conditions")
    if any(c not in CONDITIONS for c in conditions):
        raise ValueError("Unknown condition")
    suite = read_json(suite_path)
    cases = validate_suite(suite)
    prompts = {c: "" if c == "B" else prompt(c[1:], selected) for c in conditions}
    run = Path(output)
    if run.exists():
        raise ValueError("Run directory exists; choose a new directory")
    sessions, templates, assignments = [], [], []
    for case in cases:
        for repeat in range(1, repeats + 1):
            for condition in conditions:
                session_id = uuid4().hex
                sessions.append({
                    "session_id": session_id,
                    "system_prompt": prompts[condition],
                    "user_turns": case["user_turns"],
                })
                assignments.append({
                    "session_id": session_id, "case_id": case["id"],
                    "scenario_id": case["scenario_id"], "repeat": repeat,
                    "condition": condition,
                })
                templates.append({
                    "session_id": session_id, "model": "", "settings": {},
                    "context_note": "", "answers": [""] * len(case["user_turns"]),
                    "usage": None,
                })
    random.SystemRandom().shuffle(sessions)
    templates_by_id = {t["session_id"]: t for t in templates}
    run.mkdir(parents=True)
    (run / "private").mkdir()
    manifest = {
        "run_id": uuid4().hex, "suite": suite, "modules": selected,
        "suite_sha256": sha256(Path(suite_path).read_bytes()).hexdigest(),
        "conditions": conditions, "repeats": repeats,
        "prompts": {c: {"text": text, "sha256": digest(text)} for c, text in prompts.items()},
        "assignments": assignments,
        "planned_model_turns": sum(len(s["user_turns"]) for s in sessions),
    }
    write_json(run / "private" / "manifest.json", manifest)
    write_jsonl(run / "sessions.jsonl", sessions)
    write_jsonl(run / "answers-template.jsonl", [templates_by_id[s["session_id"]] for s in sessions])
    return manifest


def validate_answers(records, manifest):
    expected = {a["session_id"]: a for a in manifest["assignments"]}
    cases = {c["id"]: c for c in manifest["suite"]["cases"]}
    actual = {}
    for record in records:
        session_id = record.get("session_id")
        if session_id not in expected or session_id in actual:
            raise ValueError("Unknown or duplicate answer session_id")
        turns = cases[expected[session_id]["case_id"]]["user_turns"]
        answers = record.get("answers")
        if not isinstance(answers, list) or len(answers) != len(turns) or not all(isinstance(a, str) and a.strip() for a in answers):
            raise ValueError("Answers must cover every turn with non-empty text")
        if not isinstance(record.get("model"), str) or not record["model"].strip():
            raise ValueError("Record a model identifier (or synthetic fixture identifier)")
        if not isinstance(record.get("settings"), dict):
            raise ValueError("settings must be an object")
        if not isinstance(record.get("context_note"), str) or not record["context_note"].strip():
            raise ValueError("Record inherited context, tools and history handling in context_note")
        actual[session_id] = record
    if set(actual) != set(expected):
        raise ValueError("Missing sessions; import a complete batch")
    if len({record["model"] for record in actual.values()}) != 1:
        raise ValueError("Use one model identifier per run; compare models in separate runs")
    if len({json.dumps(record["settings"], sort_keys=True) for record in actual.values()}) != 1:
        raise ValueError("Keep recorded settings fixed across conditions")
    return actual


def make_review(run_path, answers_path, kind):
    if kind not in ("model", "synthetic"):
        raise ValueError("Choose model or synthetic sample kind")
    run = Path(run_path)
    if (run / "review.json").exists() or (run / "private" / "labels.json").exists():
        raise ValueError("Review exists; preserve it and use a new run")
    manifest = read_json(run / "private" / "manifest.json")
    records = read_jsonl(answers_path)
    answers = validate_answers(records, manifest)
    items, labels = [], {}
    for case in manifest["suite"]["cases"]:
        for repeat in range(1, manifest["repeats"] + 1):
            assignments = [a for a in manifest["assignments"] if a["case_id"] == case["id"] and a["repeat"] == repeat]
            random.SystemRandom().shuffle(assignments)
            candidates = []
            for assignment in assignments:
                label = uuid4().hex
                labels[label] = assignment
                candidates.append({
                    "label": label,
                    "answers": answers[assignment["session_id"]]["answers"],
                    "ratings": dict.fromkeys(METRICS),
                    "notes": "",
                })
            items.append({
                "case_id": case["id"], "scenario_id": case["scenario_id"], "repeat": repeat,
                "user_turns": case["user_turns"], "criteria": case["criteria"],
                "candidates": candidates,
            })
    review = {"run_id": manifest["run_id"], "kind": kind, "items": items}
    write_json(run / "private" / "labels.json", labels)
    write_jsonl(run / "private" / "answers.jsonl", records)
    write_json(run / "private" / "review-original.json", review)
    write_json(run / "review.json", review)
    return review


def summarize(run_path, review_path=None):
    run = Path(run_path)
    manifest = read_json(run / "private" / "manifest.json")
    labels = read_json(run / "private" / "labels.json")
    original = read_json(run / "private" / "review-original.json")
    review = read_json(review_path or run / "review.json")
    if review.get("run_id") != manifest["run_id"] or review.get("kind") != original["kind"]:
        raise ValueError("Review identity/kind differs from imported records")
    expected_items = {(item["case_id"], item["repeat"]): item for item in original["items"]}
    observed_items, rows = set(), []
    seen_labels = set()
    for item in review["items"]:
        key = (item["case_id"], item["repeat"])
        if key not in expected_items or key in observed_items:
            raise ValueError("Unknown or duplicate review item")
        observed_items.add(key)
        source = expected_items[key]
        for field in ("scenario_id", "user_turns", "criteria"):
            if item[field] != source[field]:
                raise ValueError("Review stimulus was changed")
        originals = {c["label"]: c for c in source["candidates"]}
        local_labels = set()
        for candidate in item["candidates"]:
            label = candidate["label"]
            if label not in originals or label in seen_labels:
                raise ValueError("Unknown, moved or duplicate review label")
            seen_labels.add(label)
            local_labels.add(label)
            if candidate["answers"] != originals[label]["answers"]:
                raise ValueError("Answers were changed during scoring")
            ratings = candidate["ratings"]
            if set(ratings) != set(METRICS) or any(v is not None and type(v) is not bool for v in ratings.values()):
                raise ValueError("Ratings must be true, false or null for each defined metric")
            if any(v is True for v in ratings.values()) and not str(candidate.get("notes", "")).strip():
                raise ValueError("Failures need notes with the relevant turn and evidence")
            rows.append({**labels[label], "ratings": ratings, "notes": candidate.get("notes", "")})
        if local_labels != set(originals):
            raise ValueError("Review is missing candidates")
    if observed_items != set(expected_items) or seen_labels != set(labels):
        raise ValueError("Review is incomplete")
    if not any(v is not None for row in rows for v in row["ratings"].values()):
        raise ValueError("No ratings recorded; null is not a pass")
    scores, pairs = {}, []
    for condition in manifest["conditions"]:
        selected = [row for row in rows if row["condition"] == condition]
        scores[condition] = {}
        for metric in METRICS:
            rated = [row["ratings"][metric] for row in selected if row["ratings"][metric] is not None]
            scores[condition][metric] = {"failures": sum(rated), "rated_sessions": len(rated), "unrated_sessions": len(selected) - len(rated)}
    for left, right in combinations(manifest["conditions"], 2):
        left_rows = {(r["case_id"], r["repeat"]): r for r in rows if r["condition"] == left}
        right_rows = {(r["case_id"], r["repeat"]): r for r in rows if r["condition"] == right}
        metrics = {}
        for metric in METRICS:
            counts = Counter()
            for key, row in left_rows.items():
                a, b = row["ratings"][metric], right_rows[key]["ratings"][metric]
                if a is None or b is None:
                    counts["unrated_pairs"] += 1
                else:
                    name = {(False, False): "both_pass", (False, True): "right_regression", (True, False): "right_improvement", (True, True): "both_fail"}[a, b]
                    counts[name] += 1
            metrics[metric] = {k: counts[k] for k in ("both_pass", "right_regression", "right_improvement", "both_fail", "unrated_pairs")}
        pairs.append({"left": left, "right": right, "metrics": metrics})
    imported = read_jsonl(run / "private" / "answers.jsonl")
    return {
        "run_id": manifest["run_id"], "kind": review["kind"],
        "model": imported[0]["model"], "settings": imported[0]["settings"],
        "context_notes": sorted({record["context_note"] for record in imported}),
        "cases": len(manifest["suite"]["cases"]),
        "scenarios": len({c["scenario_id"] for c in manifest["suite"]["cases"]}),
        "sessions": len(rows), "repeats": manifest["repeats"],
        "inference": "Descriptive development results only; no non-inferiority conclusion.",
        "scores": scores, "paired": pairs, "details": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("prompt")
    render.add_argument("--version", choices=VERSIONS, default="0.3")
    render.add_argument("--modules", default="FJE")
    build = sub.add_parser("build-skill")
    build.add_argument("--version", choices=VERSIONS, default="0.3")
    build.add_argument("--output", type=Path, default=ROOT / "prompts/skills/dog-adhd")
    build.add_argument("--check", action="store_true")
    prep = sub.add_parser("prepare")
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--suite", type=Path, default=ROOT / "evals/attention-cases.json")
    prep.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    prep.add_argument("--repeats", type=int, default=1)
    prep.add_argument("--modules", default="FJE")
    review = sub.add_parser("review")
    review.add_argument("--run", type=Path, required=True)
    review.add_argument("--answers", type=Path, required=True)
    review.add_argument("--kind", choices=("model", "synthetic"), required=True)
    report = sub.add_parser("report")
    report.add_argument("--run", type=Path, required=True)
    report.add_argument("--review", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prompt":
            print(prompt(args.version, args.modules))
        elif args.command == "build-skill":
            print(build_skill(args.version, args.output, args.check))
        elif args.command == "prepare":
            manifest = prepare(args.out, args.suite, args.conditions, args.repeats, args.modules)
            print(json.dumps({"sessions": len(manifest["assignments"]), "planned_model_turns": manifest["planned_model_turns"], "model_calls_made": 0}))
        elif args.command == "review":
            make_review(args.run, args.answers, args.kind)
            print(args.run / "review.json")
        elif args.command == "report":
            print(json.dumps(summarize(args.run, args.review), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
