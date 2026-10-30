#!/usr/bin/env python3
"""Run one safeguard against a made-up situation, in a throwaway folder, and print what the
assistant would be told. claims.ini uses this to prove each safeguard still fires.

usage: python3 tools/check_hooks.py <case>
cases: session-strict, at-limit, over-limit, outside-drafts, repeat, broken-event,
       gate-gimp, gate-signed-once, gate-yes, gate-changed, gate-expired, gate-sealed,
       gate-free, gate-fail-closed, gate-read
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
FLEET = TOOLS.parent / "docs" / "examples" / "fleet-workalong.md"    # network strict
BAKERY = TOOLS.parent / "docs" / "examples" / "bakery-workalong.md"  # level new: 2 attempts
# The first real session with a workalong.md ran exactly this, unasked.
GIMP = "sudo -n snap install gimp 2>&1 | tail -3; snap list gimp"
APT = "sudo apt-get install -y gimp"


def hook(project, which, event):
    r = subprocess.run([sys.executable, "-I", str(project / "tools" / "hooks.py"), which],
                       input=event if isinstance(event, str) else json.dumps(event),
                       capture_output=True, text=True, timeout=30,
                       env=dict(os.environ, CLAUDE_PROJECT_DIR=str(project)))
    out = r.stdout.strip()
    spec = json.loads(out)["hookSpecificOutput"] if out else {}
    if spec.get("permissionDecision") == "deny":
        told = "DENIED: " + spec["permissionDecisionReason"]
    else:
        told = spec.get("additionalContext") or "(silent)"
    return f"exit={r.returncode}\n{told}\n{r.stderr.strip()}"


def verdict(told):
    """One word per step, so a claim can check the whole story on one line."""
    if "DENIED" in told and "no signature can allow" in told:
        return "refused"
    if "DENIED" in told:
        return "stopped"
    if "isn't a signature" in told:
        return "not-a-signature"
    if "ran out of time" in told:
        return "expired"
    if "signed:" in told:
        return "signed"
    return "allowed" if "(silent)" in told else "other"


def before(project, command):
    return hook(project, "before-tool", {"session_id": "t", "tool_name": "Bash",
                                          "tool_input": {"command": command}})


def typed(project, text):
    return hook(project, "prompt", {"session_id": "t", "prompt": text})


def write(project, rel):
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("draft\n")
    return hook(project, "after-edit", {"session_id": "t", "tool_name": "Write",
                                        "tool_input": {"file_path": str(path)}})


def main(case):
    with tempfile.TemporaryDirectory() as tmp:
        project = pathlib.Path(tmp)
        shutil.copytree(TOOLS, project / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        strict = case == "session-strict" or case.startswith("gate-")
        shutil.copy(FLEET if strict else BAKERY, project / "workalong.md")
        grants = project / ".zipline" / "grants.json"
        if case == "session-strict":
            print(hook(project, "session-start", {"session_id": "t", "source": "startup"}))
        elif case == "at-limit":
            write(project, "drafts/menu/menu-v1.html")
            print(write(project, "drafts/menu/menu-v2.html"))
        elif case == "over-limit":
            for n in (1, 2):
                write(project, f"drafts/menu/menu-v{n}.html")
            print(write(project, "drafts/menu/menu-v3.html"))
        elif case == "outside-drafts":
            # Three folders deep, like a real draft, so only the drafts/ check can keep it quiet.
            # The first version used notes/menu-v9.html, and a different check silenced it.
            print(write(project, "notes/menu/menu-v9.html"))
        elif case == "repeat":
            for text in ("no, that's not it", "make the title bigger", "it's still wrong"):
                out = typed(project, text)
            print(out)
        elif case == "broken-event":
            print(hook(project, "prompt", "this is not json"))
        elif case == "gate-gimp":            # the incident: must stop, with the specifics
            print(before(project, GIMP))
        elif case == "gate-signed-once":     # sign, it runs once, then it's stopped again
            steps = [before(project, GIMP), typed(project, "install gimp"),
                     before(project, GIMP), before(project, GIMP)]
            print("RESULT " + " ".join(verdict(x) for x in steps))
        elif case == "gate-yes":             # "yes" is not a signature
            steps = [before(project, GIMP), typed(project, "yes, go ahead"), before(project, GIMP)]
            print("RESULT " + " ".join(verdict(x) for x in steps))
        elif case == "gate-changed":         # signed the snap install, then tried apt instead
            steps = [before(project, GIMP), typed(project, "install gimp"), before(project, APT)]
            print("RESULT " + " ".join(verdict(x) for x in steps))
        elif case == "gate-expired":         # a request nobody signed in time
            first = before(project, GIMP)
            data = json.loads(grants.read_text())
            data[0]["created"] -= 3600
            grants.write_text(json.dumps(data))
            steps = [first, typed(project, "install gimp"), before(project, GIMP)]
            print("RESULT " + " ".join(verdict(x) for x in steps))
        elif case == "gate-read":            # looking at the journal is fine; changing it isn't
            steps = [before(project, "tail -n 20 journal/2026-10.md"),
                     before(project, "echo forged >> journal/2026-10.md")]
            print("RESULT " + " ".join(verdict(x) for x in steps))
        elif case == "gate-sealed":          # the journal can't be rewritten, signed or not
            print(hook(project, "before-tool", {"session_id": "t", "tool_name": "Write",
                       "tool_input": {"file_path": str(project / "journal" / "2026-10.md")}}))
        elif case == "gate-free":            # ordinary work isn't gated
            steps = [hook(project, "before-tool", {"session_id": "t", "tool_name": "Write",
                          "tool_input": {"file_path": str(project / "drafts/menu/menu-v1.html")}}),
                     before(project, "python3 tools/look.py drafts/menu/menu-v1.html")]
            print("RESULT " + " ".join(verdict(x) for x in steps))
        elif case == "gate-fail-closed":     # if the gate can't decide, nothing runs
            print(hook(project, "before-tool", "this is not json"))
        else:
            print(__doc__)
            return 2
        journal = list((project / "journal").glob("*.md"))
        if journal:
            print("journal:\n" + journal[0].read_text().strip().split("\n\n", 2)[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
