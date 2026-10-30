"""Prove every claim can fail: break each safeguard on purpose, in a throwaway copy, and check
that its claim goes red. A claim that stays green with its safeguard broken protects nothing.

usage: python3 tools/check_claims_can_fail.py        (takes a minute)

Adding a claim? Add the sabotage that should turn it red, here. Three of the first eleven only
became real checks after this caught them: a test path that something else silenced, a
sabotage that missed a second layer, and a crash that looked like silence.
"""
import pathlib, re, shutil, subprocess, sys, tempfile

REPO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
SABOTAGE = {  # claim-name fragment: (file, old, new) or a shell command
    "settings in front of the assistant": ("tools/hooks.py", "network is STRICT", "network is strict"),
    "announced on the last attempt": ("tools/hooks.py", "elif count == limit:", "elif count == limit + 1:"),
    "going past the limit": ("tools/hooks.py", 'journal("over-limit"', 'journal("over"'),
    'second "still wrong"': ("tools/hooks.py", 'if state["cues"] >= 2:', 'if state["cues"] >= 3:'),
    "outside drafts/": ("tools/hooks.py", 'or rel.parts[0] != "drafts":', ':'),
    "broken event never stops": ("tools/hooks.py", "        handlers[event_name](event)\n    except Exception as e:",
                                 "        handlers[event_name](event)\n    except ZeroDivisionError as e:"),
    "points at a missing file": ("tools/look.py", "if not target.exists():", "if False:"),
    "can't be weakened": ("tools/settings.py", 'settings["always-ask"] = list(ALWAYS_ASK) + settings["also-ask"]',
                          'settings["always-ask"] = settings["also-ask"]'),
    "newline in an answer": ("docs/form.js", 'return String(s || "").replace(/[\\r\\n]+/g, " ").replace(/\\s+/g, " ").trim();', 'return String(s || "");'),
    "format description is in git": "git rm -q --cached docs/workalong.md",
    "business's own files stay out": (".gitignore", "/journal/\n", ""),
}

def run(copy):
    out = subprocess.run([sys.executable, "-I", "tools/claimcheck.py"], cwd=copy,
                         capture_output=True, text=True, timeout=600).stdout
    return [l.split("✗", 1)[1].strip() for l in out.splitlines() if "✗" in l]

ok = True
for target, how in SABOTAGE.items():
    with tempfile.TemporaryDirectory() as tmp:
        copy = pathlib.Path(tmp) / "z"
        shutil.copytree(REPO, copy, ignore=shutil.ignore_patterns(".git", "journal", ".zipline",
                                                                  "previews", "__pycache__"))
        subprocess.run("git init -q && git add -A", shell=True, cwd=copy, check=True)
        if isinstance(how, str):
            subprocess.run(how, shell=True, cwd=copy, check=True)
        else:
            f, old, new = how
            text = (copy / f).read_text()
            assert text.count(old) == 1, f"sabotage text not found once: {old!r}"
            (copy / f).write_text(text.replace(old, new))
        failed = run(copy)
        hit = [c for c in failed if target in c]
        others = [c for c in failed if target not in c]
        verdict = ("RED as it should" if not others else "RED (+knock-on)") if hit else "WRONG"
        ok &= verdict.startswith("RED")
        print(f"{verdict:<16} broke: {target:<36} failed: {failed}")
sys.exit(0 if ok else 1)
