# Decentralized_Voting_System2

## Run Local Stack (Auto Start + Deploy)

Use this to avoid blockchain/backend contract mismatch after node restarts.

### Start everything

```powershell
python start_local_stack.py
```

Windows quick launcher:

```powershell
start.bat
```

This command will:
- Start Hardhat node on port 8545 if needed
- Deploy `Voting.sol` to localhost
- Start backend on port 5000 with the deployed `CONTRACT_ADDRESS`
- Save state in `.runtime/dev_stack_state.json`

### Stop everything started by script

```powershell
python stop_local_stack.py
```

Windows quick launcher:

```powershell
stop.bat
```

Logs:
- `.runtime/hardhat-node.log`
- `.runtime/backend.log`
