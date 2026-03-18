import json
import os
import signal
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / ".runtime" / "dev_stack_state.json"


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_pid(pid: int) -> None:
    if not is_pid_running(pid):
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        os.kill(pid, signal.SIGTERM)


def main() -> int:
    if not STATE_FILE.exists():
        print("No state file found. Nothing to stop.")
        return 0

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        print("State file is unreadable. Nothing stopped.")
        return 1

    backend_pid = int(state.get("backend_pid", 0) or 0)
    node_pid = int(state.get("node_pid", 0) or 0)

    if backend_pid:
        stop_pid(backend_pid)
        print(f"Stopped backend process PID {backend_pid} (if it was running).")

    if node_pid and state.get("node_started_here", False):
        stop_pid(node_pid)
        print(f"Stopped Hardhat node PID {node_pid} (if it was running).")
    elif node_pid:
        print("Hardhat node was not started by start_local_stack.py; leaving it running.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
