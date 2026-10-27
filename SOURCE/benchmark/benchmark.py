"""Time the real grading pipeline against the 100-responses-in-two-minutes target.

Runs `run_grading_job` -- the same code the web interface uses -- on a throwaway
database, so the timing includes batching, validation and saving, not just the
API call. The provider, model and key come from an instructor's saved settings
(or from .env when that instructor has none), and nothing is written to the real
database.

The responses are the 12 synthetic samples in sample_data/, repeated with fresh
student IDs to reach each size. Repetition does not help the model: every batch
is a separate request with no shared context.

    python benchmark/benchmark.py                   # sizes 10 50 100
    python benchmark/benchmark.py --sizes 100 200
    python benchmark/benchmark.py --instructor 1

Each size uses about size/10 API calls, so the default run makes 16.
"""
import argparse
import csv
import json
import os
import shutil
import sqlite3
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SOURCE))

from app import create_app  # noqa: E402
from qayyem.db import get_db, init_db, open_connection  # noqa: E402
from qayyem.jobs import run_grading_job  # noqa: E402

TARGET_SECONDS = 120
TARGET_SIZE = 100
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _load_samples():
    with open(SOURCE / "sample_data" / "sample_responses.csv", encoding="utf-8") as fh:
        rows = [r["response"] for r in csv.DictReader(fh)]
    text = (SOURCE / "sample_data" / "ideal_answer.txt").read_text(encoding="utf-8")
    ideal = text.split("RUBRIC")[0].split("=\n", 1)[1].strip()
    rubric = text.split("RUBRIC")[1].split("QUESTION PUT")[0].split("=\n", 1)[1].strip()
    return rows, ideal, rubric


def _copy_instructor(real_db, instructor_id, app):
    src = sqlite3.connect(real_db)
    src.row_factory = sqlite3.Row
    row = src.execute("SELECT * FROM instructor WHERE id = ?", (instructor_id,)).fetchone()
    src.close()
    if row is None:
        raise SystemExit("No instructor with id " + str(instructor_id) + " in " + real_db)
    with app.app_context():
        init_db()
        db = get_db()
        db.execute(
            "INSERT INTO instructor (id, email, password_hash, full_name, ai_provider, "
            "ai_model, api_key_enc) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (row["id"], row["email"], row["password_hash"], row["full_name"],
             row["ai_provider"], row["ai_model"], row["api_key_enc"]),
        )
        db.commit()


def _seed(db_path, instructor_id, size, samples, ideal, rubric):
    conn = open_connection(db_path)
    cur = conn.execute(
        "INSERT INTO assignment (instructor_id, title, ideal_answer, rubric, max_score, "
        "status, progress_total) VALUES (?, ?, ?, ?, 10, 'pending', ?)",
        (instructor_id, "benchmark_" + str(size), ideal, rubric, size),
    )
    assignment_id = cur.lastrowid
    for i in range(size):
        conn.execute(
            "INSERT INTO student_response (assignment_id, student_id, response_text, "
            "row_number) VALUES (?, ?, ?, ?)",
            (assignment_id, "B" + str(size).zfill(3) + str(i + 1).zfill(4),
             samples[i % len(samples)], i + 1),
        )
    conn.commit()
    conn.close()
    return assignment_id


def _summarise(db_path, assignment_id):
    conn = open_connection(db_path)
    status, error = conn.execute(
        "SELECT status, error_message FROM assignment WHERE id = ?", (assignment_id,)
    ).fetchone()
    rows = conn.execute(
        "SELECT s.response_text, g.score, g.error, g.model_name FROM grading_result g "
        "JOIN student_response s ON s.id = g.response_id WHERE s.assignment_id = ?",
        (assignment_id,),
    ).fetchall()
    conn.close()
    scores = [r["score"] for r in rows if r["score"] is not None]

    # Each sample answer appears several times, each copy in a separate request.
    # A consistent grader gives every copy the same score.
    by_answer = {}
    for r in rows:
        if r["score"] is not None:
            by_answer.setdefault(r["response_text"], []).append(r["score"])
    repeated = [v for v in by_answer.values() if len(v) > 1]
    spreads = [max(v) - min(v) for v in repeated]
    return {
        "status": status,
        "error": error,
        "graded": len(scores),
        "failed": sum(1 for r in rows if r["error"]),
        "model": rows[0]["model_name"] if rows else None,
        "mean_score": round(statistics.mean(scores), 2) if scores else None,
        "identical_scores": sum(1 for d in spreads if d == 0),
        "repeated_answers": len(repeated),
        "max_spread": max(spreads) if spreads else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sizes", type=int, nargs="+", default=[10, 50, 100])
    parser.add_argument("--instructor", type=int, default=1,
                        help="whose saved provider settings to use")
    parser.add_argument("--database", default=str(SOURCE / "instance" / "qayyem.sqlite3"),
                        help="real database to read those settings from (read only)")
    args = parser.parse_args()

    samples, ideal, rubric = _load_samples()
    workdir = tempfile.mkdtemp(prefix="qayyem-bench-")
    db_path = os.path.join(workdir, "bench.sqlite3")
    app = create_app({"DATABASE": db_path})
    _copy_instructor(args.database, args.instructor, app)

    runs = []
    try:
        for size in args.sizes:
            assignment_id = _seed(db_path, args.instructor, size, samples, ideal, rubric)
            started = time.perf_counter()
            run_grading_job(app, assignment_id)
            elapsed = time.perf_counter() - started
            summary = _summarise(db_path, assignment_id)
            summary.update(size=size, seconds=round(elapsed, 1),
                           per_response=round(elapsed / size, 2))
            runs.append(summary)
            print("{size:>4} responses  {seconds:>6.1f} s  ({per_response:.2f} s each)  "
                  "graded {graded}, failed {failed}, status {status}".format(**summary))
            if summary["repeated_answers"]:
                print("      consistency: {identical_scores}/{repeated_answers} repeated "
                      "answers always got the same score (largest spread {max_spread} "
                      "of 10)".format(**summary))
            if summary["error"]:
                print("      " + summary["error"][:200])
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    RESULTS_DIR.mkdir(exist_ok=True)
    report = {
        "run_at_utc": stamp,
        "batch_size": app.config["GRADING_BATCH_SIZE"],
        "target": str(TARGET_SIZE) + " responses in " + str(TARGET_SECONDS) + " s",
        "runs": runs,
    }
    out = RESULTS_DIR / ("benchmark_" + stamp + ".json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved " + str(out.relative_to(SOURCE)))

    target = next((r for r in runs if r["size"] == TARGET_SIZE), None)
    if target:
        met = target["status"] == "complete" and target["seconds"] <= TARGET_SECONDS
        print("Target (" + report["target"] + "): " + ("MET" if met else "NOT MET"))


if __name__ == "__main__":
    main()
