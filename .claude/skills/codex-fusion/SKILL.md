---
name: codex-fusion
description: Hand Fusion placement or assembly work to the long-lived Codex session that has the Fusion MCP (model and thread id in run_codex_visible.ps1), or ask it how to do something in Fusion. Use when a Fusion edit fails through the API from here (occurrence moves revert, nested placements, configured designs) or the user asks to delegate to Codex.
---

# Delegate Fusion work to Codex

Codex keeps a long-lived Fusion thread. It is good at native occurrence placement, joints in nested assemblies
and configured designs, where API edits from here have reverted or been ignored. It is a second Fusion writer:
while it runs, you make no Fusion edits.

Files: `C:\Users\ryanh\tools\_agent\codex-fusion\` (`BRIEF.md` holds its standing rules; `work\` holds the
briefs and reports).

## Steps
1. Write the brief to `work\resume_prompt_<N+1>.txt` (next free N). Include:
   - the goal and the acceptance test, in numbers (for example the overlap limit in mm³, the poses to test);
   - the documents it may save, by name; it stops on anything outside the list;
   - the report file to write, `work\<topic>_report.md`, with the measurements;
   - "Do not launch or kill Fusion; the watchdog does."
   No double quotes anywhere in the brief: it is passed as one argument.
2. Stop any earlier Codex window first: find `powershell.exe` processes whose command line contains
   `run_codex_visible.ps1` (`Get-CimInstance Win32_Process`) and end each with `taskkill /PID <id> /T /F`.
3. Launch it outside this session's job object, so it survives the turn:
   `Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine = 'powershell.exe -NoExit -ExecutionPolicy Bypass -File C:\Users\ryanh\tools\_agent\codex-fusion\run_codex_visible.ps1'}`.
   The script runs the newest `work\resume_prompt_*.txt`.
4. Wait for the report file with a background loop (`run_in_background`), not by polling. Typing into the Codex
   window does not work when the laptop lid is closed; to steer it, write a new brief and restart it.
5. Check its work yourself: re-snapshot and run the checks (the `fusion-change` skill, steps 3 to 7). A report
   is a claim, not evidence.
6. When it is done, close its window (step 2), so Codex sessions do not pile up.
