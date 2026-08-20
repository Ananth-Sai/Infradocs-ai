"""Run the adversarial eval 3 times to measure stability at temperature=0."""
import os
import subprocess
import shutil
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

for run in range(1, 4):
    print(f"\n{'='*50}")
    print(f"  RUN {run}/3")
    print(f"{'='*50}")
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "eval_harness.py"), "adversarial_v1"],
        cwd=PROJECT_ROOT,
        capture_output=False,
    )
    # Copy the results file inside eval_results/
    src = os.path.join(PROJECT_ROOT, "eval_results", "eval_results_adversarial_v1.json")
    dst = os.path.join(PROJECT_ROOT, "eval_results", f"eval_results_adversarial_v1_run{run}.json")
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  -> Saved as {dst}")
    else:
        print(f"  [ERROR] Source file not found: {src}")

print("\n\nAll 3 runs complete. Compare the run files in eval_results/ to check stability.")
