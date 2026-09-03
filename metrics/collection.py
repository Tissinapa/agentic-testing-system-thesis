import json
import os
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path("results")

def load_agent_results(filepath: Path) -> dict:
    with open(filepath) as f :
        data = json.load(f)
    return{
        "framework": "AI Agent",
        "app": data["meta"]["target"],
        "mode": data["meta"].get("mode", "black"),
        "tests_generated": data["summary"]["test_cases_generated"],
        "tests_executed": data["summary"]["tests_executed"],
        "tests_passed": max(0, data["summary"]["tests_executed"] - data["summary"]["bugs_detected"]),
        "bugs_detected": data["summary"]["bugs_detected"],
        "false_positives": data["summary"]["false_positives"],
        "endpoints_covered": data["summary"]["endpoints_covered"],
        "token_usage": data["meta"]["token_usage"],
        "iterations": data["meta"]["iterations"],
        "bugs": [b["verdict"] for b in data.get("bugs", [])],
    
    }
    
def load_robot_results(filepath: Path) -> dict:
    import xml.etree.ElementTree as ET
    tree = ET.parse(filepath)
    root = tree.getroot()

    total = 0
    passed = 0
    failed = 0

    for test in root.iter("test"):
        total += 1
        status = test.find("status")
        if status is not None:
            if status.get("status") == "PASS":
                passed += 1
            else:
                failed += 1

    # Detect app from parent folder name
    app = "java" if "java" in filepath.parent.name.lower() else "python"

    return {
        "framework": "Robot Framework",
        "app": app,
        "mode": "black",
        "tests_generated": total,
        "tests_executed": total,
        "tests_passed": passed,
        "bugs_detected": failed,
        "false_positives": 0,
        "endpoints_covered": None,
        "token_usage": 0,
        "iterations": 1,
        "bugs": [],
    }

def load_pytest_results(filepath: Path) -> dict:
    with open(filepath) as f:
        data = json.load(f)
    
    summary = data.get("summary", {})
    total = data.get("summary", {}).get("total", 0)
    failed = data.get("summary", {}).get("failed", 0)
    passed = data.get("summary", {}).get("passed", 0)

    app = "java" if "java" in filepath.stem.lower() else "python"

    
    return {
        "framework": "Pytest + HTTPX",
        "app": app,
        "mode": "black",
        "tests_generated": total,
        "tests_executed": total,
        "tests_passed": passed,
        "bugs_detected": failed,
        "false_positives": 0,
        "endpoints_covered": None,
        "token_usage": 0,
        "iterations": 1,
        "bugs": [],
    }

def load_schemathesis_results(filepath: Path) -> dict:
    import xml.etree.ElementTree as ET
    tree = ET.parse(filepath)
    root = tree.getroot()

    total = int(root.get("tests", 0))
    errors = int(root.get("errors", 0))
    failures = int(root.get("failures", 0))
    failed = errors + failures
    passed = passed = max(0, total - failed)

    # Use folder name directly as app identifier
    folder_name = filepath.parent.name.lower()
    app = folder_name  # java, python, java_os, python_os

    return {
        "framework": "Schemathesis",
        "app": app,
        "mode": "black",
        "tests_generated": total,
        "tests_executed": total,
        "tests_passed": passed,
        "bugs_detected": failed,
        "false_positives": 0,
        "endpoints_covered": None,
        "token_usage": 0,
        "iterations": 1,
        "bugs": [],
    }    
def collect_all_results() ->list[dict]:
    
    results = []

    # Agent results
    agent_dir = RESULTS_DIR / "agent"
    if agent_dir.exists():
        for f in sorted(agent_dir.glob("*.json")):
            try:
                results.append(load_agent_results(f))
                print(f"Loaded agent: {f.name}")
            except Exception as e:
                print(f"Warning: could not load {f.name}: {e}")

    # Robot Framework results — java and python subfolders
    for app in ["javaAPI", "pythonAPI"]:
        robot_dir = RESULTS_DIR / "robot" / app
        if robot_dir.exists():
            for f in sorted(robot_dir.glob("output*.xml")):
                try:
                    results.append(load_robot_results(f))
                    print(f"Loaded robot: {f.name}")
                except Exception as e:
                    print(f"Warning: could not load {f.name}: {e}")

    # Pytest results
    pytest_dir = RESULTS_DIR / "pytest"
    if pytest_dir.exists():
        for f in sorted(pytest_dir.glob("*.json")):
            try:
                results.append(load_pytest_results(f))
                print(f"Loaded pytest: {f.name}")
            except Exception as e:
                print(f"Warning: could not load {f.name}: {e}")

    # Schemathesis results — java and python subfolders
    for app_folder in ["java", "python", "java_os", "python_os"]:
        schema_dir = RESULTS_DIR / "schemathesis" / app_folder
        if schema_dir.exists():
            for f in sorted(schema_dir.glob("*.xml")):
                try:
                    results.append(load_schemathesis_results(f))
                    print(f"Loaded schemathesis: {f.name}")
                except Exception as e:
                    print(f"Warning: could not load {f.name}: {e}")

    return results

def save_results(results: list[dict]):
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_frameworks": len(set(r["framework"] for r in results)),
        "total_runs": len(results),
        "results": results,
    }
    output_path = RESULTS_DIR / "metrics_summary.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nMetrics saved to {output_path}")
    return output

if __name__ == "__main__":
    print("Collecting results from all frameworks...\n")
    results = collect_all_results()
    summary = save_results(results)
    print(f"\nTotal runs collected: {summary['total_runs']}")