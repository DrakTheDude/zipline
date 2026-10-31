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
    "rules for this kind of work": ("tools/hooks.py", 'f"(profiles/{s[\'profile\']}.md), on top of CLAUDE.md:", "", profile_rules]',
                                    'f"(profiles/{s[\'profile\']}.md), on top of CLAUDE.md:", ""]'),
    "misspelled profile is reported": ("tools/settings.py", '    if settings["profile"] not in profile_names():',
                                       '    if False:'),
    "nothing is committed on main": ("tools/gates.py", 'if team != "solo" and branch in main_branches(top):', "if False:"),
    "too big to review": ("tools/gates.py", 'if len(files) > s["commit-files"]:', "if False:"),
    "main isn't pushed to": ("tools/gates.py", 'if team != "solo" and on_main:', "if False:"),
    "push stops while claims fail": ("tools/gates.py", "            if failing:\n", "            if False:\n"),
    "changing GitHub through gh": ("tools/gates.py", "if tuple(args[:2]) in GH_WRITES or writes_api:", "if False:"),
    "plugins are turned on": ("tools/setup.py", 'wanted = {f"{p}@{MARKETPLACE}": p in meta["plugins"] for p in sorted(every)}',
                              'wanted = {f"{p}@{MARKETPLACE}": True for p in sorted(every)}'),
    "keeps the person's own local": ("tools/setup.py", '    local["enabledPlugins"] = {**local.get("enabledPlugins", {}), **wanted}',
                                     '    local = {"enabledPlugins": wanted}'),
    "who reviews it reach the settings": ("docs/form.js", "lines.push(`team: ${a.team}`);", "{}"),
    "starts knowing who reviews": ("tools/hooks.py", '    if s["team"] != "solo":\n        lines.append(f"- team is', '    if False:\n        lines.append(f"- team is'),
    "announced on the last attempt": ("tools/hooks.py", "elif count == limit:", "elif count == limit + 1:"),
    "going past the limit": ("tools/hooks.py", 'journal("over-limit"', 'journal("over"'),
    'second "still wrong"': ("tools/hooks.py", "if cue and sum(recent) >= 2:", "if cue and sum(recent) >= 3:"),
    "long ago don't make": ("tools/hooks.py", "CUE_WINDOW = 4 ", "CUE_WINDOW = 100 "),
    "explaining isn't someone correcting": ("tools/hooks.py", "CUE_MAX_WORDS = 60", "CUE_MAX_WORDS = 100000"),
    "pasted text is someone else's": ("tools/hooks.py", 'own = PASTED.sub(" ", text)', "own = text"),
    "outside drafts/": ("tools/hooks.py", 'or rel.parts[0] != "drafts":', ':'),
    "broken event never stops": ("tools/hooks.py", "        handlers[event_name](event)\n    except Exception as e:",
                                 "        handlers[event_name](event)\n    except ZeroDivisionError as e:"),
    "points at a missing file": ("tools/look.py", "if not target.exists():", "if False:"),
    "can't be weakened": ("tools/settings.py", 'settings["always-ask"] = list(ALWAYS_ASK) + settings["also-ask"]',
                          'settings["always-ask"] = settings["also-ask"]'),
    "newline in an answer": ("docs/form.js", 'return String(s || "").replace(/[\\r\\n]+/g, " ").replace(/\\s+/g, " ").trim();', 'return String(s || "");'),
    "format description is in git": "git rm -q --cached docs/workalong.md",
    "business's own files stay out": (".gitignore", "/journal/\n", ""),
    "GIMP install stops": ("tools/gates.py", "if tool in SOURCES and args and args[0] in INSTALL_WORDS | REMOVE_WORDS:",
                           "if False:"),
    "run once, then it stops": ("tools/hooks.py", 'live["status"], live["used_at"] = "used", time.time()',
                                 'live["used_at"] = time.time()'),
    '"yes" is not a signature': ("tools/hooks.py", 'if g["phrase"] == typed), None)',
                                 'if g["phrase"] == typed or YES.match(typed)), None)'),
    "changed command after signing": ("tools/hooks.py", "raw = json.dumps([tool, action], sort_keys=True)",
                                      "raw = json.dumps([tool], sort_keys=True)"),
    "after the request expired": ("tools/hooks.py", 'if g["status"] in ("pending", "granted") and now - start > ttl:',
                                  'if False:'),
    "can be read, never changed": ("tools/gates.py", "if not words or pathlib.Path(words[0]).name not in READ_ONLY:",
                                   "if True:"),
    "writing the journal directly": ("tools/gates.py", "if in_project(path, root) and inside(path, root, *SEALED):",
                                     "if False:"),
    "ordinary work isn't gated": ("tools/hooks.py", "    if gate is None:\n        return\n    if gate.blocked:",
                                  "    if gate is None:\n        gate = gates.Gate('check', 'this')\n    if gate.blocked:"),
    "gate itself fails": ("tools/hooks.py", 'if event_name == "before-tool":', "if False:"),
    # Puts back the original bug: the description the assistant rewords is part of what's signed.
    "rewording its own description": ("tools/hooks.py",
                                      "action = {k: v for k, v in tool_input.items() if k not in NOT_THE_ACTION}",
                                      "action = tool_input"),
    "near-miss signature": ("tools/hooks.py", "    if near:\n", "    if False:\n"),
    "subagent's report can't sign": ("tools/hooks.py", 'if SYSTEM_MESSAGE.match(str(event.get("prompt", ""))):',
                                     "if False:"),
    "same rule for writing files": ("tools/gates.py", "found = [write_gate(path, root) for path in written_paths(words, cwd) + redirect_targets(part, cwd)]",
                                    "found = []"),
    "here-document is": ("tools/gates.py", "        return m.group(0) if prog in SHELLS else \"\\n\"",
                         "        return \"\\n\""),
    "latest request, not one": ("tools/hooks.py", 'recent = [g for g in pending if g["created"] >= since]',
                                "recent = pending"),
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
