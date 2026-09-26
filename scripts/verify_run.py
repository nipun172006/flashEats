"""Run the assessment checks and refresh the small checked-in evidence snapshot."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-09-26"
PARTITION = ROOT / "data" / "processed" / f"run_date={RUN_DATE}"
EVIDENCE = ROOT / "evidence"


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(scenario):
    result = subprocess.run(
        [sys.executable, "run_pipeline.py", "--run-date", RUN_DATE, "--chaos", scenario],
        cwd=ROOT, capture_output=True, text=True,
    )
    status = json.loads((ROOT / "logs" / f"latest_status_{RUN_DATE}.json").read_text())
    return result, status


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    EVIDENCE.mkdir(exist_ok=True)
    unit = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT,
                          capture_output=True, text=True)
    require(unit.returncode == 0, unit.stdout + unit.stderr)
    cases = []
    first, status = run_case("none")
    require(first.returncode == 0 and status["status"] == "SUCCESS", first.stdout + first.stderr)
    digest1 = checksum(PARTITION / "order_journey.csv")
    second, status = run_case("none")
    require(second.returncode == 0, second.stdout + second.stderr)
    digest2 = checksum(PARTITION / "order_journey.csv")
    require(digest1 == digest2, "Same-date rerun changed order_journey")
    cases.append({"scenario": "normal_then_rerun", "exit_codes": [0, 0],
                  "first_sha256": digest1, "second_sha256": digest2, "identical": True})
    for scenario in ["missing_column", "stale_data"]:
        before = {p.name: checksum(p) for p in PARTITION.iterdir() if p.is_file()}
        result, status = run_case(scenario)
        after = {p.name: checksum(p) for p in PARTITION.iterdir() if p.is_file()}
        require(result.returncode == 2 and status["status"] == "FAILED", result.stdout + result.stderr)
        require(before == after, f"{scenario} modified processed output")
        require(any(r["status"] == "FAIL" for r in status["validation"]), "Failure check was not recorded")
        cases.append({"scenario": scenario, "exit_code": result.returncode,
                      "processed_files_unchanged": True, "failed_check_saved": True})
        shutil.copyfile(ROOT / "logs" / f"latest_status_{RUN_DATE}.json", EVIDENCE / f"failure_{scenario}.json")
    result, status = run_case("duplicate_order")
    require(result.returncode == 0, result.stdout + result.stderr)
    require(checksum(PARTITION / "order_journey.csv") == digest1, "Exact duplicate changed the final journey")
    cases.append({"scenario": "duplicate_order", "exit_code": 0, "journey_unchanged": True})
    # Leave the directory and checked-in snapshot in the normal, non-chaos state.
    final, status = run_case("none")
    require(final.returncode == 0 and status["chaos"] == "none", final.stdout + final.stderr)
    for source, target in {
        "metrics.json": "final_metrics.json", "validation_report.json": "final_validation_report.json",
        "run_manifest.json": "final_run_manifest.json", "evidence_table.csv": "final_evidence_table.csv",
        "kpi_definition_comparison.csv": "kpi_definition_comparison.csv",
        "duplicate_sensitivity.json": "duplicate_sensitivity.json",
    }.items():
        shutil.copyfile(PARTITION / source, EVIDENCE / target)
    for name in ["orders", "interactions", "interventions"]:
        shutil.copyfile(ROOT / "data" / "raw" / f"run_date={RUN_DATE}" / "exceptions" / f"{name}_duplicate_rows.csv",
                        EVIDENCE / f"{name}_duplicate_rows.csv")
    shutil.copyfile(ROOT / "logs" / f"latest_status_{RUN_DATE}.json", EVIDENCE / "final_attempt_status.json")
    (EVIDENCE / "verification.json").write_text(json.dumps({"logical_run_date": RUN_DATE,
        "data_contract_tests": "PASS", "unit_test_output": unit.stdout + unit.stderr, "cases": cases}, indent=2))
    print("Verified normal run, identical rerun, both failure gates, duplicate handling and data-contract tests.")
    print("Evidence snapshot refreshed. Final partition is a successful normal run.")


if __name__ == "__main__":
    main()
