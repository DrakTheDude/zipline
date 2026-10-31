#!/usr/bin/env python3
"""Read workalong.md, fill in defaults, and check it for mistakes.

usage: python3 tools/settings.py [path/to/workalong.md]

Prints the settings in effect. Exit code = the number of problems found, so 0 means the file
is fine (or missing, in which case the defaults apply). The format is in docs/workalong.md.

Other tools import load() so every part of zipline reads the settings the same way.
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"
FORMAT = 1

LEVEL_ATTEMPTS = {"new": 2, "burned": 2, "pattern": 4}
DEFAULTS = {
    "zipline": FORMAT, "profile": "business", "business": "", "level": "", "attempts": 3, "explain": "normal",
    "network": "standard", "allow": [], "users": "just-me", "reaches": [], "also-ask": [],
    "team": "solo", "commit-files": 15,
}
CHOICES = {
    "level": {"new", "burned", "pattern"},
    "explain": {"more", "normal", "less"},
    "network": {"standard", "strict"},
    "users": {"just-me", "staff"},
    "team": {"solo", "pair", "team"},
}
REACHES = {"email", "calendar", "accounts", "files", "shell", "remote-machines"}
LISTS = {"allow", "reaches", "also-ask"}
# Fixed at every level. workalong.md can add to these (also-ask), never remove one.
ALWAYS_ASK = ("send", "promise", "delete", "spend", "install")


def parse(text):
    """Split into (settings dict, house rules text, problems)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["the settings block must start with a line of three dashes (---)"]
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, text, ["the settings block never ends: add a closing line of ---"]
    raw, problems = {}, []
    for n, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if not sep:
            problems.append(f"line {n}: expected 'setting: value', got {line.strip()!r}")
        elif key in raw:
            problems.append(f"line {n}: {key} is set twice")
        else:
            raw[key] = value.strip()
    return raw, "\n".join(lines[end + 1:]).strip(), problems


def load(path=None):
    """Return (settings, house rules, problems). A missing file means defaults, not a problem."""
    path = pathlib.Path(path) if path else ROOT / "workalong.md"
    settings = dict(DEFAULTS, **{k: list(v) for k, v in DEFAULTS.items() if isinstance(v, list)})
    settings["always-ask"] = list(ALWAYS_ASK)
    if not path.exists():
        return settings, "", []
    raw, rules, problems = parse(path.read_text(errors="replace"))
    for key, value in raw.items():
        if key not in DEFAULTS:
            problems.append(f"unknown setting {key!r} (known: {', '.join(DEFAULTS)})")
        elif key in LISTS:
            settings[key] = [v.strip() for v in value.split(",") if v.strip()]
        elif key in ("zipline", "attempts", "commit-files"):
            if not value.isdigit():
                problems.append(f"{key} must be a whole number, got {value!r}")
            else:
                settings[key] = int(value)
        elif key in CHOICES and value not in CHOICES[key]:
            problems.append(f"{key} must be one of {', '.join(sorted(CHOICES[key]))}, got {value!r}")
        else:
            settings[key] = value
    if settings["profile"] not in profile_names():
        problems.append(f"profile must be one of {', '.join(profile_names())}, got "
                        f"{settings['profile']!r}; using business")
        settings["profile"] = "business"
    if settings["zipline"] != FORMAT:
        problems.append(f"this is format {settings['zipline']}, these tools read format {FORMAT}")
    if "attempts" not in raw and settings["level"] in LEVEL_ATTEMPTS:
        settings["attempts"] = LEVEL_ATTEMPTS[settings["level"]]
    if not 1 <= settings["attempts"] <= 10:
        problems.append(f"attempts must be between 1 and 10, got {settings['attempts']}")
    if settings["commit-files"] < 1:
        problems.append("commit-files must be at least 1")
        settings["commit-files"] = DEFAULTS["commit-files"]
    unknown = [r for r in settings["reaches"] if r not in REACHES]
    if unknown:
        problems.append(f"reaches: don't know {', '.join(unknown)} (known: {', '.join(sorted(REACHES))})")
    if settings["allow"] and settings["network"] != "strict":
        problems.append("allow only means something with network: strict")
    removed = [a for a in settings["also-ask"] if a.lower().startswith(("no ", "not ", "skip ", "never ask", "don't", "dont ", "do not"))]
    if removed:
        problems.append(f"also-ask can only add things to ask about, not remove them: {removed}")
    settings["always-ask"] = list(ALWAYS_ASK) + settings["also-ask"]
    return settings, rules, problems


def profile_names():
    return sorted(p.stem for p in PROFILES.glob("*.md"))


def load_profile(name):
    """Return (settings, rules) for one kind of work, from profiles/<name>.md: which folders
    and tools it needs, and the working rules the assistant is given at session start."""
    path = PROFILES / f"{name}.md"
    if not path.exists():  # reported by load(); the core rules in CLAUDE.md still apply
        return {"folders": [], "tools": [], "plugins": [], "for": "(profile file missing)"}, ""
    raw, rules, _ = parse(path.read_text(errors="replace"))
    meta = {k: [v.strip() for v in raw.get(k, "").split(",") if v.strip()]
            for k in ("folders", "tools", "plugins")}
    meta["for"] = raw.get("for", "")
    return meta, rules


def main(argv):
    path = pathlib.Path(argv[0]) if argv else ROOT / "workalong.md"
    settings, rules, problems = load(path)
    print(f"{path}: " + ("found" if path.exists() else "not found, using defaults"))
    for key in ("profile", "business", "level", "attempts", "explain", "network", "allow", "users",
                "reaches", "team", "commit-files", "always-ask"):
        value = settings[key]
        value = ", ".join(value) if isinstance(value, list) else value
        print(f"  {key:<10} {value if value != '' else '-'}")
    if rules:
        print(f"  house rules: {len(rules.splitlines())} lines")
    for p in problems:
        print(f"PROBLEM: {p}")
    return len(problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
