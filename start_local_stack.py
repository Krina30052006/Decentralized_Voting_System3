import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BLOCKCHAIN_DIR = ROOT / "blockchain"
BACKEND_DIR = ROOT / "backend"
RUNTIME_DIR = ROOT / ".runtime"
STATE_FILE = RUNTIME_DIR / "dev_stack_state.json"
NODE_LOG = RUNTIME_DIR / "hardhat-node.log"
BACKEND_LOG = RUNTIME_DIR / "backend.log"

NODE_HOST = "127.0.0.1"
NODE_PORT = 8545
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 5000


def get_npx_command() -> str:
    return "npx.cmd" if os.name == "nt" else "npx"


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def wait_for_port(host: str, port: int, timeout_seconds: int) -> bool:
    started = time.time()
    while time.time() - started < timeout_seconds:
        if is_port_open(host, port):
            return True
        time.sleep(0.5)
    return False


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
    if pid == os.getpid():
        return

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
            )
        except subprocess.TimeoutExpired:
            pass
    else:
        os.kill(pid, signal.SIGTERM)


def find_listening_pid_on_port(port: int) -> int:
    if os.name != "nt":
        return 0

    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return 0

    target = f":{port}"
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if target not in line or "LISTENING" not in line:
            continue

        parts = line.split()
        if not parts:
            continue
        try:
            return int(parts[-1])
        except ValueError:
            continue

    return 0


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    RUNTIME_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def deploy_contract() -> str:
    cmd = [get_npx_command(), "hardhat", "run", "scripts/deploy.js", "--network", "localhost"]
    result = subprocess.run(
        cmd,
        cwd=BLOCKCHAIN_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    match = re.search(r"Voting contract deployed to:\s*(0x[a-fA-F0-9]{40})", output)
    if not match:
        print("Deploy output:\n" + output)
        raise RuntimeError("Could not parse deployed contract address.")

    return match.group(1)


def start_hardhat_node() -> int:
    RUNTIME_DIR.mkdir(exist_ok=True)
    with NODE_LOG.open("a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            [get_npx_command(), "hardhat", "node"],
            cwd=BLOCKCHAIN_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    return proc.pid


def start_backend(contract_address: str) -> int:
    RUNTIME_DIR.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["CONTRACT_ADDRESS"] = contract_address

    with BACKEND_LOG.open("a", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=BACKEND_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )
    return proc.pid


def main() -> int:
    print("Starting local voting stack...")
    state = load_state()

    old_backend_pid = int(state.get("backend_pid", 0) or 0)
    if old_backend_pid:
        stop_pid(old_backend_pid)

    # If another backend instance is already bound to 5000, stop it so startup is deterministic.
    existing_backend_port_pid = find_listening_pid_on_port(BACKEND_PORT)
    if existing_backend_port_pid:
        stop_pid(existing_backend_port_pid)
        time.sleep(1)

    node_started_here = False
    node_pid = int(state.get("node_pid", 0) or 0)

    if is_port_open(NODE_HOST, NODE_PORT):
        print(f"Hardhat node already running at {NODE_HOST}:{NODE_PORT}.")
    else:
        print("Starting Hardhat node...")
        node_pid = start_hardhat_node()
        node_started_here = True
        if not wait_for_port(NODE_HOST, NODE_PORT, timeout_seconds=30):
            raise RuntimeError("Hardhat node did not start on port 8545 within 30 seconds.")

    print("Deploying Voting contract...")
    contract_address = deploy_contract()
    print(f"Contract deployed at {contract_address}")

    print("Starting backend...")
    backend_pid = start_backend(contract_address)
    if not wait_for_port(BACKEND_HOST, BACKEND_PORT, timeout_seconds=20):
        raise RuntimeError("Backend did not start on port 5000 within 20 seconds. Check .runtime/backend.log")

    state = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "node_pid": node_pid,
        "backend_pid": backend_pid,
        "contract_address": contract_address,
        "node_started_here": node_started_here,
        "logs": {
            "node": str(NODE_LOG.relative_to(ROOT)),
            "backend": str(BACKEND_LOG.relative_to(ROOT)),
        },
    }
    save_state(state)

    print("Stack is ready.")
    print(f"Backend: http://127.0.0.1:5000")
    print(f"Contract: {contract_address}")
    print(f"Node log: {NODE_LOG}")
    print(f"Backend log: {BACKEND_LOG}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Startup failed: {exc}")
        raise SystemExit(1)
