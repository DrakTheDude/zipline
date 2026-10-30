#!/usr/bin/env python3
"""Run one safeguard against a made-up situation, in a throwaway folder, and print what the
assistant would be told. claims.ini uses this to prove each safeguard still fires.

usage: python3 tools/check_hooks.py <case>
cases: session-strict, at-limit, over-limit, outside-drafts, repeat, broken-event
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
FLEET = TOOLS.parent / "docs" / "examples" / "fleet-workalong.md"
BAKERY = TOOLS.parent / "docs" / "examples" / "bakery-workalong.md"  # level new: 2 attempts


def hook(project, which, event):
    r = subprocess.run([sys.executable, "-I", str(project / "tools" / "hooks.py"), which],
                       input=event if isinstance(event, str) else json.dumps(event),
                       capture_output=True, text=True, timeout=30,
                       env=dict(os.environ, CLAUDE_PROJECT_DIR=str(project)))
    out = r.stdout.strip()
    told = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else "(silent)"
    return f"exit={r.returncode}\n{told}\n{r.stderr.strip()}"


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
        shutil.copy(FLEET if case == "session-strict" else BAKERY, project / "workalong.md")
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
                out = hook(project, "prompt", {"session_id": "t", "prompt": text})
            print(out)
        elif case == "broken-event":
            print(hook(project, "prompt", "this is not json"))
        else:
            print(__doc__)
            return 2
        journal = list((project / "journal").glob("*.md"))
        if journal:
            print("journal:\n" + journal[0].read_text().strip().split("\n\n", 2)[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
