#!/usr/bin/env python3
"""zipline's safeguards. Claude Code runs this at fixed points (see .claude/settings.json);
the assistant doesn't call it and can't skip it.

    python3 tools/hooks.py session-start   when a session opens: put the settings in front
                                           of the assistant, so it doesn't have to remember
    python3 tools/hooks.py prompt          on each message the person types: notice when
                                           they're repeating themselves
    python3 tools/hooks.py before-tool     before anything runs: stop actions that need the
                                           person's signature (see tools/gates.py)
    python3 tools/hooks.py after-edit      after anything runs: count draft versions against
                                           the attempt limit, and journal signed actions

Each reads Claude Code's event as JSON on stdin and writes what the assistant should know as
JSON on stdout. Everything worth keeping goes in journal/YYYY-MM.md, which only this file
writes: the safeguards record what happened, the assistant doesn't get to.

A safeguard must never break the session it's guarding: any error is reported to the
assistant as text and the hook exits 0.
"""
import difflib, hashlib, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parent.parent)
STATE = ROOT / ".zipline" / "state.json"
JOURNAL = ROOT / "journal"
sys.path.insert(0, str(ROOT / "tools"))
import settings as settings_mod  # noqa: E402
import gates  # noqa: E402

GRANTS = ROOT / ".zipline" / "grants.json"
PENDING_TTL = 30 * 60   # a request waits this long for a signature
GRANTED_TTL = 5 * 60    # a signature is good for one use within this window

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
    "asked": "an action was stopped until the person signs for it",
    "signed": "the person typed the signature",
    "not-signed": "the person said yes, but not with the signature",
    "used": "a signed action was allowed to run, once",
    "done": "a signed action finished",
    "expired": "a request or signature ran out of time unused",
    "refused": "an action no signature can allow was stopped",
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
    lines.append("\nSome actions stop until the person signs: sending, installing, deleting or "
                 "overwriting their files, spending, and anything the settings add. When one "
                 "stops, you'll be told the specifics and the phrase; pass both on in plain "
                 "words. A 'yes' isn't a signature. Never type the phrase yourself.")
    lines.append("\njournal/ is written by these safeguards. Don't write to it yourself.")
    say("SessionStart", "\n".join(lines))
    journal("session", (f"{event.get('source') or 'started'} · level {s['level'] or '-'} · "
                        f"{s['attempts']} attempts · network "
                        f"{s['network']}" + ("" if found else " · no workalong.md, defaults")))


# --- signatures: the person types "<verb> <target>" to let one specific action run once ------

def load_grants():
    try:
        grants = json.loads(GRANTS.read_text())
    except (OSError, ValueError):
        grants = []
    now, keep = time.time(), []
    for g in grants:
        ttl = PENDING_TTL if g["status"] == "pending" else GRANTED_TTL
        start = g["created"] if g["status"] == "pending" else g.get("granted_at", 0)
        if g["status"] in ("pending", "granted") and now - start > ttl:
            journal("expired", f"{g['phrase']} ({g['status']}, unused)")
            g["status"] = "expired"
        if g["status"] in ("pending", "granted") or now - g["created"] < 24 * 3600:
            keep.append(g)
    return keep


def save_grants(grants):
    GRANTS.parent.mkdir(exist_ok=True)
    GRANTS.write_text(json.dumps(grants, indent=1))


# Fields the assistant writes about an action, rather than the action itself. Claude Code's Bash
# tool carries a `description` the assistant rewords on every call; the first version hashed it,
# so a signed command run again with a reworded description was stopped again: sign, stopped,
# sign again. The fixture never caught it because it sent one-key events that never varied.
NOT_THE_ACTION = {"description"}


def fingerprint(tool, tool_input):
    """The exact action. A signature covers this and nothing else: if the command changes after
    signing, the specifics changed, and it needs signing again."""
    action = {k: v for k, v in tool_input.items() if k not in NOT_THE_ACTION}
    raw = json.dumps([tool, action], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def normalise(text):
    text = re.sub(r"\s+", " ", str(text)).strip().strip("`'\"").strip()
    return text.rstrip(".!").lower()


YES = re.compile(r"^(y|yes|yep|yeah|ok|okay|sure|go|go ahead|do it|proceed|approved?|fine|"
                 r"confirmed?|sign(ed)?|please do)\b", re.I)


def before_tool(event):
    tool, tool_input = event.get("tool_name", ""), event.get("tool_input") or {}
    s = settings_mod.load()[0]
    gate = gates.classify(tool, tool_input, s, ROOT)
    if gate is None:
        return
    if gate.blocked:
        journal("refused", f"{tool}: {gate.blocked[:80]}")
        deny(f"zipline: not allowed, and no signature can allow it. {gate.blocked}")
        return
    fp = fingerprint(tool, tool_input)
    grants = load_grants()
    live = next((g for g in grants if g["fingerprint"] == fp and g["status"] == "granted"), None)
    if live:
        live["status"], live["used_at"] = "used", time.time()
        save_grants(grants)
        journal("used", live["phrase"])
        state = load_state(event.get("session_id"))
        state["running"] = {"fingerprint": fp, "phrase": live["phrase"]}
        save_state(state)
        return
    if not any(g["fingerprint"] == fp and g["status"] == "pending" for g in grants):
        grants.append({"phrase": gate.phrase, "details": gate.details, "fingerprint": fp,
                       "tool": tool, "status": "pending", "created": time.time()})
        save_grants(grants)
        journal("asked", f"{gate.phrase} · " + "; ".join(gate.details))
    deny("zipline: stopped. This needs the person's signature before it runs.\n"
         f"Tell them plainly what it will do: " + "; ".join(gate.details) + ".\n"
         f"Then tell them: to go ahead, type exactly: {gate.phrase}\n"
         "Don't type it for them, and don't change the command to get around this. If they "
         "sign, run exactly the same command again; a different command needs a new signature. "
         "If they'd rather not, offer another way.")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def sign(event):
    """If the message is a signature for a pending request, grant it. Returns True if this
    message was about a signature, so it isn't also read as the person repeating themselves."""
    typed = normalise(event.get("prompt", ""))
    grants = load_grants()
    pending = [g for g in grants if g["status"] == "pending"]
    if not pending:
        save_grants(grants)
        if any(g["status"] == "expired" and g["phrase"] == typed for g in grants):
            say("UserPromptSubmit", f"zipline: the person typed '{typed}', but that request "
                "ran out of time unsigned, so it doesn't count. Tell them it expired; if they "
                "still want it, try the action again and a fresh request will come up.")
            return True
        return False
    match = next((g for g in reversed(pending) if g["phrase"] == typed), None)
    if match:
        match["status"], match["granted_at"] = "granted", time.time()
        save_grants(grants)
        journal("signed", f'"{match["phrase"]}"')
        say("UserPromptSubmit", f"zipline: signed: {match['phrase']}. You may now run exactly "
            "the action it covers, once, in the next 5 minutes. Then tell the person what "
            "happened, and if it failed, show how.")
        return True
    save_grants(grants)
    # Close but not exact ("install gimp please") is the dangerous case: the person believes they
    # signed, and nothing said otherwise. The first version stayed silent on it.
    near = next((g for g in reversed(pending) if g["phrase"] in typed or
                 difflib.SequenceMatcher(None, typed, g["phrase"]).ratio() > 0.8), None)
    if near:
        journal("not-signed", f'"{typed[:40]}" is close to, not exactly, "{near["phrase"]}"')
        say("UserPromptSubmit", f"zipline: close, but not a signature: the person typed "
            f"'{typed}', and it has to be exactly: {near['phrase']}. Tell them it didn't count "
            "yet, and why; don't run the action.")
        return True
    if YES.match(typed):
        phrases = ", ".join(sorted({g["phrase"] for g in pending}))
        journal("not-signed", f'"{typed[:40]}" while waiting for: {phrases}')
        say("UserPromptSubmit", f"zipline: that isn't a signature. Waiting for the person to "
            f"type exactly: {phrases}. Say so plainly; don't run the action.")
        return True
    return False


# Claude Code also delivers its own messages through this event: when a subagent finishes, its
# report arrives wrapped in <task-notification>. Found in a real session, where a subagent's
# report quoting "connect example.org" was read as a near-miss signature. A report is written by
# the assistant's side, so it must never sign: the model can't sign its own contract.
SYSTEM_MESSAGE = re.compile(r"^\s*<(task-notification|system-reminder|command-[\w-]+|"
                            r"local-command-[\w-]+|[\w-]+-notification)\b", re.I)


def prompt(event):
    if SYSTEM_MESSAGE.match(str(event.get("prompt", ""))):
        return  # not typed by the person: can't sign, isn't a near miss, isn't them repeating
    if sign(event):
        return
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
    state = load_state(event.get("session_id"))
    running = state.get("running")
    if running and running["fingerprint"] == fingerprint(tool, event.get("tool_input") or {}):
        response = event.get("tool_response") or {}
        failed = isinstance(response, dict) and (response.get("interrupted") or response.get("is_error"))
        journal("done", f"{running['phrase']}" + (" · reported a failure" if failed else ""))
        state.pop("running")
        save_state(state)
    if tool not in ("Write", "Edit", "MultiEdit"):
        return
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
    handlers = {"session-start": session_start, "prompt": prompt, "after-edit": after_edit,
                "before-tool": before_tool}
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
                      "after-edit": "PostToolUse", "before-tool": "PreToolUse"}.get(event_name)
        if event_name == "before-tool":
            # Failing closed: if the gate can't decide, the action doesn't run.
            deny(msg + ". The signature check couldn't run, so this action is stopped. Tell "
                 "the person.")
            return 0
        if hook_event:
            say(hook_event, msg + ". Tell the person: this safeguard didn't run, so don't "
                "rely on it for this step.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
