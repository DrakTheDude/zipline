#!/usr/bin/env python3
"""zipline's safeguards. Claude Code runs this at fixed points (see .claude/settings.json);
the assistant doesn't call it and can't skip it.

    python3 tools/hooks.py session-start   when a session opens: put the settings in front
                                           of the assistant, so it doesn't have to remember
    python3 tools/hooks.py prompt          on each message the person types: notice when
                                           they're repeating themselves
    python3 tools/hooks.py after-edit      after the assistant writes a file: count draft
                                           versions against the attempt limit

Each reads Claude Code's event as JSON on stdin and writes what the assistant should know as
JSON on stdout. Everything worth keeping goes in journal/YYYY-MM.md, which only this file
writes: the safeguards record what happened, the assistant doesn't get to.

A safeguard must never break the session it's guarding: any error is reported to the
assistant as text and the hook exits 0.
"""
import difflib, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parent.parent)
STATE = ROOT / ".zipline" / "state.json"
JOURNAL = ROOT / "journal"
sys.path.insert(0, str(ROOT / "tools"))
import settings as settings_mod  # noqa: E402

VERSION = re.compile(r"-v(\d+)\.[A-Za-z0-9]+$")
# Words people use when the last answer missed. One on its own means little ("again" is
# ordinary), so the nudge needs two in a session, or a message that nearly repeats an earlier one.
CUES = re.compile(r"\b(still (wrong|not|the same|broken)|i said|i already (said|told)|not what i"
                  r"|that'?s not (it|right|what)|same (thing|problem|mistake)|(doesn'?t|didn'?t) work"
                  r"|try again|again\?|no,? (that|it'?s|not)|why (is|does|did) it (still|keep))\b", re.I)


# --- journal: the record the safeguards keep -------------------------------------------------

EVENTS = {  # an event name is an API: add, don't rename
    "session": "a session started, with these settings",
    "attempt": "a new version of a draft",
    "limit": "the attempt limit was reached; a reset is next",
    "over-limit": "a version beyond the limit",
    "in-place": "a draft version was overwritten instead of saved as a new one",
    "repeating": "the person may be repeating themselves",
    "problem": "a safeguard couldn't do its job",
}


def journal(event, text):
    JOURNAL.mkdir(exist_ok=True)
    now = time.localtime()
    path = JOURNAL / time.strftime("%Y-%m.md", now)
    if not path.exists():
        path.write_text(f"# Journal, {time.strftime('%B %Y', now)}\n\nWritten by zipline's "
                        "safeguards, not by the assistant. One line per thing that happened.\n\n")
    with path.open("a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M', now)}  {event:<11} {text}\n")


# --- state between events (machinery: dotted folder, the person never needs it) -------------

def load_state(session):
    try:
        state = json.loads(STATE.read_text())
    except (OSError, ValueError):
        state = {}
    if state.get("session") != session:
        state = {"session": session, "prompts": [], "cues": 0, "edits": {}}
    return state


def save_state(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state))


def say(event_name, text):
    """Tell the assistant something, through Claude Code."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event_name,
                                             "additionalContext": text}}))


# --- the three safeguards ---------------------------------------------------------------------

def session_start(event):
    s, rules, problems = settings_mod.load()
    found = (ROOT / "workalong.md").exists()
    lines = ["zipline settings for this session (from workalong.md, loaded automatically; "
             "these apply to everything you do here, not only drafts):" if found else
             "zipline: no workalong.md here, so the defaults apply:"]
    for key in ("business", "level", "attempts", "explain", "network", "allow", "users", "reaches"):
        value = s[key]
        value = ", ".join(value) if isinstance(value, list) else value
        if value != "" and value != []:
            lines.append(f"- {key}: {value}")
    lines.append("- always ask first (wait for an explicit yes that covers the specifics): "
                 + "; ".join(s["always-ask"]))
    if s["network"] == "strict":
        allowed = ", ".join(s["allow"]) or "nothing"
        lines.append(f"- network is STRICT: anything that goes out over the network (downloads, "
                     f"installs from a store, uploads, API calls) needs the person's OK unless it "
                     f"only reaches: {allowed}. Say exactly where it would go before asking.")
    if rules:
        lines += ["", "House rules, in the owner's words (stricter than a setting for their job, "
                      "they win):", rules]
    missing = [f for f in ("brand", "drafts", "ready") if not (ROOT / f).is_dir()]
    if missing:
        lines.append(f"\nThe workspace isn't set up ({', '.join(missing)} missing). Before the "
                     "first draft, run `python3 tools/setup.py`.")
    if problems:
        lines.append("\nworkalong.md has problems, tell the person: " + "; ".join(problems))
    lines.append("\njournal/ is written by these safeguards. Don't write to it yourself.")
    say("SessionStart", "\n".join(lines))
    journal("session", (f"{event.get('source') or 'started'} · level {s['level'] or '-'} · "
                        f"{s['attempts']} attempts · network "
                        f"{s['network']}" + ("" if found else " · no workalong.md, defaults")))


def prompt(event):
    text = str(event.get("prompt", ""))
    state = load_state(event.get("session_id"))
    reasons = []
    if CUES.search(text):
        state["cues"] += 1
        if state["cues"] >= 2:
            reasons.append("they've signalled twice now that the result isn't right")
    short = re.sub(r"\s+", " ", text.lower()).strip()
    if len(short) > 15:
        for earlier in state["prompts"]:
            if difflib.SequenceMatcher(None, short, earlier).ratio() > 0.8:
                reasons.append("this message nearly repeats an earlier one")
                break
        state["prompts"] = (state["prompts"] + [short])[-8:]
    save_state(state)
    if reasons:
        journal("repeating", f'"{text.strip()[:70]}"' + ("…" if len(text.strip()) > 70 else ""))
        say("UserPromptSubmit", "zipline: the person may be going round in circles: "
            + " and ".join(reasons) + ". Per CLAUDE.md, don't make another attempt at the same "
            "thing: reset (stop and say so, say back the goal and the inputs you assumed, ask "
            "the one question that would change the approach). If they've already said 'keep "
            "going', carry on.")


def after_edit(event):
    tool = event.get("tool_name", "")
    path = (event.get("tool_input") or {}).get("file_path", "")
    if not path:
        return
    try:
        rel = pathlib.Path(path).resolve().relative_to(ROOT.resolve())
    except ValueError:
        return
    if len(rel.parts) < 3 or rel.parts[0] != "drafts":
        return
    job = rel.parts[1]
    folder = ROOT / "drafts" / job
    limit = settings_mod.load()[0]["attempts"]
    versions = [int(m.group(1)) for f in folder.iterdir() if (m := VERSION.search(f.name))]
    count = max(versions, default=0)
    state = load_state(event.get("session_id"))
    if tool in ("Edit", "MultiEdit") and VERSION.search(rel.name):
        state["edits"][job] = state["edits"].get(job, 0) + 1
        save_state(state)
        journal("in-place", f"{rel} edited in place")
        count += state["edits"][job]
        note = (f"You changed {rel.name} in place. Each new version should be a new -vN file, "
                f"so the person can go back, and so the count stays honest. ")
    else:
        note = ""
    if count < limit:
        journal("attempt", f"{rel} · {count} of {limit}")
        say("PostToolUse", f"{note}zipline: attempt {count} of {limit} on drafts/{job}.")
    elif count == limit:
        journal("limit", f"drafts/{job} · {count} of {limit}, reset is next")
        say("PostToolUse", f"{note}zipline: that was attempt {count} of {limit} on drafts/{job}, "
            "the limit. Don't make another version. Show this one, and if it still isn't right, "
            "reset (CLAUDE.md, 'Reset: start from the other end').")
    else:
        journal("over-limit", f"{rel} · {count} of {limit}")
        say("PostToolUse", f"{note}zipline: attempt {count} on drafts/{job}, over the limit of "
            f"{limit}. Unless the person explicitly said to keep going, stop and reset now, "
            "and tell them this went past the limit.")


def main(argv):
    event_name = argv[0] if argv else ""
    handlers = {"session-start": session_start, "prompt": prompt, "after-edit": after_edit}
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
        handlers[event_name](event)
    except Exception as e:  # noqa: BLE001 - a safeguard must never take the session down
        msg = f"zipline safeguard '{event_name}' failed: {type(e).__name__}: {e}"
        try:
            journal("problem", msg)
        except Exception:  # noqa: BLE001
            pass
        print(msg, file=sys.stderr)
        # Tell the assistant too. A safeguard that fails quietly looks exactly like one that
        # checked and had nothing to say, and a claim was once fooled by that.
        hook_event = {"session-start": "SessionStart", "prompt": "UserPromptSubmit",
                      "after-edit": "PostToolUse"}.get(event_name)
        if hook_event:
            say(hook_event, msg + ". Tell the person: this safeguard didn't run, so don't "
                "rely on it for this step.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
