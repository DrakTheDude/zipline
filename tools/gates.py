#!/usr/bin/env python3
"""Which actions need the person's signature, and what they'd be signing.

classify(tool_name, tool_input, settings, root) returns None when an action is free to run,
or a Gate: the verb and target the person types ("install gimp", "email james", "delete
logo.svg"), and the specifics they're agreeing to.

The rule for anything unclear is to ask. A signature that wasn't needed costs a few seconds;
a send that should have been signed can't be taken back.

What this can't see: it reads commands and tool names, so an action dressed up as something
else (a script that sends email without saying so) gets past it. It guards against an
assistant that's confident and wrong, not one that's trying to hide what it does.

    python3 tools/gates.py '<shell command>'     show what a command would need, for testing
"""
import json, os, pathlib, re, shlex, subprocess, sys, tempfile
from dataclasses import dataclass, field


@dataclass
class Gate:
    verb: str                      # what the person types first: install, email, delete...
    target: str                    # what it acts on: gimp, james, logo.svg
    details: list = field(default_factory=list)   # the specifics they're agreeing to
    blocked: str = ""              # set when no signature can allow this at all

    @property
    def phrase(self):
        return f"{self.verb} {self.target}"


# Where package managers download from, so strict network mode can say where things go.
SOURCES = {
    "apt": ("Ubuntu/Debian archive", ["archive.ubuntu.com", "security.ubuntu.com"]),
    "apt-get": ("Ubuntu/Debian archive", ["archive.ubuntu.com", "security.ubuntu.com"]),
    "snap": ("the Snap Store", ["api.snapcraft.io"]),
    "flatpak": ("Flathub", ["dl.flathub.org"]),
    "dnf": ("Fedora mirrors", ["mirrors.fedoraproject.org"]),
    "yum": ("RHEL/CentOS mirrors", ["mirrorlist.centos.org"]),
    "brew": ("Homebrew", ["formulae.brew.sh", "ghcr.io"]),
    "winget": ("the winget catalogue", ["cdn.winget.microsoft.com"]),
    "choco": ("the Chocolatey catalogue", ["community.chocolatey.org"]),
    "pip": ("PyPI", ["pypi.org", "files.pythonhosted.org"]),
    "pip3": ("PyPI", ["pypi.org", "files.pythonhosted.org"]),
    "pipx": ("PyPI", ["pypi.org", "files.pythonhosted.org"]),
    "npm": ("the npm registry", ["registry.npmjs.org"]),
    "gem": ("RubyGems", ["rubygems.org"]),
    "cargo": ("crates.io", ["crates.io"]),
}
INSTALL_WORDS = {"install", "add"}
REMOVE_WORDS = {"remove", "purge", "uninstall", "erase", "autoremove"}
NETWORK_TOOLS = {"curl", "wget", "ssh", "scp", "rsync", "sftp", "ftp", "nc", "ncat", "telnet",
                 "git", "docker", "podman"} | set(SOURCES)
GIT_NETWORK = {"clone", "fetch", "pull", "push", "ls-remote", "submodule"}
# Package-manager subcommands that reach the network. "snap list" or "pip show" don't, and
# asking for a signature to look at what's installed teaches people to sign without reading.
PKG_NETWORK = {"install", "add", "update", "upgrade", "refresh", "download", "search", "info",
               "find", "fetch", "sync", "outdated", "pull"}
DELETE_TOOLS = {"rm", "rmdir", "shred", "unlink", "truncate"}
MAIL_TOOLS = {"sendmail", "mail", "mailx", "mutt", "swaks"}
# Folders where the assistant's own work lives: deleting or overwriting there is free.
CLAIMCHECK = pathlib.Path(__file__).resolve().parent / "claimcheck.py"
SCRATCH = ("drafts", "previews")
# The person's own things: overwriting these needs their signature.
OWNER = ("brand", "ready", "workalong.md", "lessons.md")
# The safeguards' own record. Nothing the assistant does may touch these, signed or not.
SEALED = (".zipline", "journal")

MCP_SEND = re.compile(r"send|post|publish|reply|forward|share|upload|create_(message|post|draft_and_send)|message", re.I)
MCP_SPEND = re.compile(r"pay|charge|refund|purchase|invoice|payment|checkout|subscribe|order", re.I)
MCP_DELETE = re.compile(r"delete|remove|trash|archive|destroy|cancel", re.I)
MCP_READ = re.compile(r"^(get|list|search|read|find|query|fetch|describe|lookup)", re.I)


def short(text, n=40):
    text = re.sub(r"[^\w.@+-]+", "-", str(text).strip().lower()).strip("-")
    return text[:n] or "it"


def segments(command):
    """Split a shell command into simple commands. Imperfect by design: when in doubt the
    caller asks, rather than guessing a command is harmless."""
    for part in re.split(r"\|\||&&|;|\||\n|`|\$\(", command):
        try:
            words = shlex.split(part, comments=True)
        except ValueError:
            words = part.split()
        while words and (words[0] in ("sudo", "doas", "env", "nohup", "time", "exec", "command")
                         or re.match(r"^\w+=", words[0]) or (words[0].startswith("-") and words[0] != "-")):
            words = words[1:]
        if words:
            yield words


def hosts_in(words):
    found = []
    for w in words:
        if m := re.match(r"^[a-z][a-z0-9+.-]*://([^/:@\s]+@)?([^/:\s]+)", w, re.I):
            found.append(m.group(2).lower())
        elif m := re.match(r"^([\w.-]+@)?([\w-]+(\.[\w-]+)+):", w):
            found.append(m.group(2).lower())
    return found


def allowed(host, allow):
    return any(host == a or host.endswith("." + a) for a in allow)


def inside(path, root, *names):
    try:
        rel = pathlib.Path(path).expanduser().resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return bool(rel.parts) and rel.parts[0] in names


def in_project(path, root):
    try:
        pathlib.Path(path).expanduser().resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


READ_ONLY = {"cat", "head", "tail", "less", "more", "grep", "egrep", "zgrep", "ls", "wc",
             "diff", "stat", "file", "cut", "sort", "uniq", "jq"}


def mentions_sealed(text):
    return any(re.search(rf"(^|[\s/'\"=]){re.escape(x)}(/|\s|$|['\"*])", text) for x in SEALED)


def touches_sealed(command):
    """True when a command could change the safeguards' record. Looking is fine: the owner may
    well ask what's in the journal. The first version blocked any mention at all, and stopped a
    plain `tail journal/*.md`."""
    if not mentions_sealed(command):
        return False
    if re.search(r">>?\s*\S*(" + "|".join(re.escape(x) for x in SEALED) + ")", command):
        return True  # writing into it with a redirect
    for part in re.split(r"\|\||&&|;|\||\n|`|\$\(", command):
        if not mentions_sealed(part):
            continue
        try:
            words = shlex.split(part)
        except ValueError:
            return True
        while words and (words[0] in ("sudo", "env") or re.match(r"^\w+=", words[0])):
            words = words[1:]
        if not words or pathlib.Path(words[0]).name not in READ_ONLY:
            return True
        if words[0] in ("sort",) and "-o" in words:
            return True
    return False


def classify_bash(command, s, root):
    strict = s["network"] == "strict"
    allow = s["allow"]
    if touches_sealed(command):
        return Gate("change", "safeguards", blocked=f"{' and '.join(SEALED)} are the safeguards' "
                    "own record. Nothing the assistant runs may change them, signed or not. "
                    "Reading them with cat, tail, grep or ls is fine.")
    gates = []
    # Files the command writes go through the same rule as the editor (write_gate). Follow `cd`
    # so `cd /other/project && git apply x.patch` is judged where it actually writes.
    cwd = root
    for part in re.split(r"\|\||&&|;|\||\n", shell_text(command)):
        try:
            words = shlex.split(part, comments=True)
        except ValueError:
            words = part.split()
        while words and (words[0] in ("sudo", "doas", "env", "nohup", "time", "exec")
                         or re.match(r"^\w+=", words[0])):
            words = words[1:]
        if not words:
            continue
        if words[0] == "cd":
            target = words[1] if len(words) > 1 else "~"
            cwd = (cwd / os.path.expandvars(os.path.expanduser(target))).resolve()
            continue
        found = [write_gate(path, root) for path in written_paths(words, cwd) + redirect_targets(part, cwd)]
        if pathlib.Path(words[0]).name == "git":
            found.append(git_gate(words, cwd, s))
        for g in found:
            if g and g.blocked:
                return g
            if g and all(g.phrase != x.phrase for x in gates):
                gates.append(g)
    for words in segments(shell_text(command)):
        tool = pathlib.Path(words[0]).name
        args = [w for w in words[1:] if not w.startswith("-")]
        if tool == "python3" and "tools/setup.py" in " ".join(words) and "--install" in words:
            gates.append(Gate("install", "setup", ["the tools tools/setup.py listed as missing",
                                                   "runs with sudo where the installer needs it"]))
            continue
        if tool in SOURCES and args and args[0] in INSTALL_WORDS | REMOVE_WORDS:
            removing = args[0] in REMOVE_WORDS
            packages = [a for a in args[1:] if not a.startswith("-")]
            name, hosts = SOURCES[tool]
            details = [f"from {name} ({tool})" if not removing else f"using {tool}"]
            if "sudo" in command.split():
                details.append("runs with sudo (administrator rights)")
            if tool == "snap" and not removing:
                details.append("snaps update themselves in the background")
            if strict and not removing:
                outside = [h for h in hosts if not allowed(h, allow)]
                if outside:
                    details.append(f"downloads from {', '.join(outside)}, which isn't on your "
                                   "allowed list")
            gates.append(Gate("uninstall" if removing else "install",
                              short(packages[0] if packages else tool), details))
            continue
        if tool in DELETE_TOOLS or tool == "mv" or (tool == "git" and args[:1] == ["clean"]) \
                or (tool == "git" and args[:2] == ["reset", "--hard"]) \
                or (tool == "find" and "-delete" in words):
            targets = args if tool in DELETE_TOOLS else args[:-1] if tool == "mv" else args
            # Free only in the assistant's own scratch space: drafts/ and previews/ here, or the
            # system's temp folder when that isn't where this project lives. (The first version
            # exempted anything under /tmp/, and a project kept in /tmp lost its logo for free.)
            if tool in DELETE_TOOLS and targets and all(
                    inside(t, root, *SCRATCH) or (not in_project(t, root)
                                                  and t.startswith(("/tmp/", "$TMPDIR")))
                    for t in targets):
                continue
            if tool == "mv" and args and inside(args[-1], root, "ready"):
                gates.append(Gate("approve", short(pathlib.Path(targets[0]).name if targets else "it"),
                                  [f"moves {' '.join(targets)} into ready/, which means you've "
                                   "approved it to go out"]))
                continue
            verb = "move" if tool == "mv" else "delete"
            gates.append(Gate(verb, short(pathlib.Path(targets[0]).name if targets else tool),
                              [f"{verb}s: {' '.join(targets) or 'see the command'}",
                               "can't be undone from here" if verb == "delete" else
                               "the original location will be empty"]))
            continue
        if tool in MAIL_TOOLS or "smtplib" in command:
            to = next((a for a in args if "@" in a), "")
            gates.append(Gate("email", short(to.split("@")[0] if to else "someone"),
                              [f"sends an email{' to ' + to if to else ''} from this computer"]))
            continue
        if tool == "git" and args[:1] == ["push"]:
            g = Gate("push", short(args[1] if len(args) > 1 else "origin"),
                     ["publishes commits to a remote repository"])
            if all(g.phrase != x.phrase for x in gates):  # the git rules may have said more
                gates.append(g)
            continue
        if tool == "gh":
            g = gh_gate(words)
            if g:
                gates.append(g)
            continue
        if tool == "curl" and re.search(r"(^|\s)(-X\s*(POST|PUT|PATCH|DELETE)|-d|--data\S*|-F|--form|-T|--upload-file)(\s|=|$)", " ".join(words)):
            host = (hosts_in(words) or ["a server"])[0]
            gates.append(Gate("send", short(host), [f"uploads or sends data to {host}"]))
            continue
        if tool in ("scp", "rsync", "sftp") and hosts_in(words[-1:]):
            host = hosts_in(words[-1:])[0]
            gates.append(Gate("upload", short(host), [f"copies files to {host}"]))
            continue
        if strict and tool in NETWORK_TOOLS:
            if tool == "git" and not set(args[:1]) & GIT_NETWORK:
                continue
            if tool in SOURCES and not set(args[:1]) & PKG_NETWORK:
                continue
            found = hosts_in(words) or (SOURCES[tool][1] if tool in SOURCES else [])
            outside = [h for h in found if not allowed(h, allow)]
            if outside or not found:
                where = ", ".join(outside) if outside else "an address this check can't read"
                gates.append(Gate("connect", short(outside[0] if outside else tool),
                                  [f"reaches {where}, which isn't on your allowed list"]))
    if not gates:
        return None
    first = gates[0]
    for extra in gates[1:]:
        first.details.append(f"also: {extra.phrase} ({'; '.join(extra.details)})")
    return first


def git_out(cwd, *args):
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def main_branches(top):
    names = {"main", "master"}
    head = git_out(top, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if "/" in head:
        names.add(head.split("/", 1)[1])
    return names


def failing_claims(top):
    """Names of failing claims in the repo's claims.ini; None if it couldn't be checked in time."""
    try:
        out = subprocess.run([sys.executable, str(CLAIMCHECK), "-f", str(top / "claims.ini"),
                              "--json"], cwd=top, capture_output=True, text=True, timeout=45).stdout
        results = json.loads(out)["claims"]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        return None
    return [r["claim"] for r in results if r["status"] == "fail"]


def git_gate(words, cwd, s):
    """The git rules from workalong.md: `team` and `commit-files`. Reviews themselves are
    GitHub's to enforce (branch rules); what can be stopped here is work reaching main without
    them, commits too big to review, and pushing work whose claims fail."""
    if len(words) > 2 and words[1] == "-C":
        cwd, words = (cwd / words[2]).resolve(), words[:1] + words[3:]
    args = [w for w in words[1:] if not w.startswith("-")]
    top = git_out(cwd, "rev-parse", "--show-toplevel") if args else ""
    if not top:
        return None
    top, team = pathlib.Path(top), s["team"]
    branch = git_out(top, "branch", "--show-current")
    if args[0] == "commit":
        if team != "solo" and branch in main_branches(top):
            return Gate("commit", branch, blocked=(
                f"with team: {team}, nothing is committed on {branch}: work reaches it through a "
                f"reviewed pull request. Make a branch named for this piece of work first "
                f"(git switch -c <slice-name>), then commit there."))
        files = set(git_out(top, "diff", "--cached", "--name-only").splitlines())
        if any(re.match(r"^-[a-zA-Z]*a[a-zA-Z]*$", w) or w == "--all" for w in words[2:]):
            files |= set(git_out(top, "diff", "--name-only").splitlines())
        files.discard("")
        if len(files) > s["commit-files"]:
            return Gate("commit", f"{len(files)} files", [
                f"commits {len(files)} files at once; the limit is {s['commit-files']} so that a "
                "person can review it", "better: split it into commits with one purpose each"])
    if args[0] == "push":
        refs = args[2:]
        targets = [r.lstrip("+").split(":")[-1].removeprefix("refs/heads/") for r in refs] or [branch]
        on_main = [t for t in targets if t in main_branches(top)]
        if team != "solo" and on_main:
            return Gate("push", on_main[0], blocked=(
                f"with team: {team}, work reaches {on_main[0]} through a pull request with "
                f"{'one review' if team == 'pair' else 'two reviews'}, not a push. Push the branch "
                f"(git push -u origin <branch>) and open a pull request."))
        if (top / "claims.ini").exists():
            failing = failing_claims(top)
            if failing:
                return Gate("push", "unchecked", blocked=(
                    "only validated work is pushed, and these claims fail: " + "; ".join(failing)
                    + ". Fix them, or change the claim if it's out of date, then push."))
            if failing is None:
                return Gate("push", short(args[1] if len(args) > 1 else "origin"), [
                    "publishes commits to a remote repository",
                    "claims.ini couldn't be checked in time, so this push is unvalidated"])
    return None


GH_WRITES = {("pr", "merge"), ("repo", "delete"), ("repo", "edit"), ("repo", "archive"),
             ("repo", "rename"), ("release", "create"), ("release", "delete")}


def gh_gate(words):
    """GitHub changes made through its command-line tool: merges, repo settings, releases, and
    API calls that write (including branch rules)."""
    args = [w for w in words[1:] if not w.startswith("-")]
    text = " ".join(words)
    writes_api = args[:1] == ["api"] and re.search(
        r"(-X|--method)[ =]?(POST|PUT|PATCH|DELETE)|\s(-f|-F|--field|--raw-field|--input)\s", text, re.I)
    if tuple(args[:2]) in GH_WRITES or writes_api:
        return Gate("change", "github", [f"changes GitHub: gh {' '.join(args[:3])}",
                                         "affects everyone who uses the repository"])
    return None


def write_gate(path, root):
    """The one rule for writing a file, whichever tool does it. The editor had this rule and the
    shell didn't: `cp` or `sed -i` into a folder outside this one went through unsigned while the
    editor asked for the same change. Found while about to update another project's notes."""
    path = str(path)
    name = short(pathlib.Path(path).name)
    if in_project(path, root) and inside(path, root, *SEALED):
        return Gate("change", "safeguards", blocked="journal/ and .zipline/ are the "
                    "safeguards' own record. Nothing the assistant writes may change them.")
    if inside(path, root, "ready"):
        return Gate("approve", name, [f"puts {pathlib.Path(path).name} in ready/, which "
                                      "means you've approved it to go out"])
    exists = pathlib.Path(path).expanduser().exists()
    if exists and inside(path, root, *OWNER):
        return Gate("overwrite", name, [f"changes your {path}", "the current version "
                                        "is replaced"])
    if not in_project(path, root) and (str(pathlib.Path(path).expanduser()).startswith(
            (tempfile.gettempdir() + os.sep, "/tmp/")) or path.startswith("/dev/")):
        return None  # the system's temp folder is scratch space, the same as for rm
    if not in_project(path, root):
        return Gate("overwrite" if exists else "write", name,
                    [f"{'changes' if exists else 'creates'} {path}, outside this folder"])
    return None


# Shell commands that write files, and which of their arguments they write to.
IN_PLACE = {"sed": ("-i", "--in-place"), "perl": ("-i", "-pi")}
GIT_WRITES = {"apply", "checkout", "restore", "reset", "am", "stash", "pull", "merge", "rebase"}


def written_paths(words, cwd):
    """Files a simple command writes, as absolute paths. Only what can be read off the command:
    a script that writes files without saying so can't be seen here."""
    tool = pathlib.Path(words[0]).name
    args = [w for w in words[1:] if not w.startswith("-")]
    out = []
    if tool in ("cp", "install", "ln", "rsync") and len(args) >= 2 and not hosts_in(args[-1:]):
        dest = cwd / os.path.expanduser(args[-1])
        # Copying into a folder writes a file named after the source: name that, not the folder.
        out += ([str(dest / pathlib.Path(a).name) for a in args[:-1]]
                if args[-1].endswith("/") or dest.is_dir() else [args[-1]])
    elif tool in ("touch", "mkdir", "tee", "truncate"):
        out += args
    elif tool == "patch":
        out.append(".")
    elif tool in IN_PLACE and any(w.startswith(IN_PLACE[tool]) for w in words[1:]):
        out += args[1:] if tool == "sed" else args
    elif tool == "dd":
        out += [w[3:] for w in words if w.startswith("of=")]
    elif tool in ("tar", "unzip") and re.search(r"(^|\s)(-\w*x|x\w*f|-d|-C)\b", " ".join(words[1:])):
        out.append(next((words[i + 1] for i, w in enumerate(words)
                         if w in ("-C", "-d") and i + 1 < len(words)), "."))
    elif tool == "git" and args[:1] and args[0] in GIT_WRITES:
        out.append(".")
    return [str((cwd / os.path.expandvars(os.path.expanduser(p))).resolve()) for p in out if p]


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\s*\2\s*(?:\n|$)", re.S)
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}


def shell_text(command):
    """The command as the shell will run it. A here-document's body is input for the program it's
    fed to, not shell syntax: a Python script's string ">> ~/x" is not a redirect. The first
    version read it as one and stopped a test script. Bodies fed to a shell are kept, because
    those really are commands."""
    def keep_or_drop(m):
        line_start = command.rfind("\n", 0, m.start()) + 1
        words = command[line_start:m.start()].split()
        prog = pathlib.Path(next((w for w in words if not re.match(r"^\w+=", w)
                                  and w not in ("sudo", "env")), "")).name
        return m.group(0) if prog in SHELLS else "\n"
    return HEREDOC.sub(keep_or_drop, command)


def redirect_targets(text, cwd):
    targets = []
    for m in re.finditer(r"(?<![<&])\d?>>?\s*([^\s;&|<>()]+)", text):
        t = m.group(1).strip("'\"")
        if t.startswith("&") or t.startswith("/dev/"):
            continue
        targets.append(str((cwd / os.path.expandvars(os.path.expanduser(t))).resolve()))
    return targets


def classify(tool_name, tool_input, s, root):
    root = pathlib.Path(root)
    tool_input = tool_input or {}
    if tool_name == "Bash":
        return classify_bash(str(tool_input.get("command", "")), s, root)
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        return write_gate(path, root) if path else None
    if tool_name == "WebFetch" and s["network"] == "strict":
        host = (hosts_in([str(tool_input.get("url", ""))]) or ["a website"])[0]
        if not allowed(host, s["allow"]):
            return Gate("connect", short(host), [f"fetches a page from {host}, which isn't on "
                                                 "your allowed list"])
    if tool_name == "WebSearch" and s["network"] == "strict":
        return Gate("connect", "web-search", ["sends a search to a web search service"])
    if tool_name.startswith("mcp__"):
        action = tool_name.split("__")[-1]
        if MCP_READ.match(action):
            return None
        who = next((str(tool_input[k]) for k in ("to", "recipient", "recipients", "email",
                    "channel", "customer", "customer_email", "user") if tool_input.get(k)), "")
        who = who.split(",")[0].split("@")[0].strip("[]'\" ") if who else action
        service = tool_name.split("__")[1] if tool_name.count("__") >= 2 else "a connected service"
        if MCP_SPEND.search(action):
            return Gate("charge", short(who), [f"{action} through {service}", "involves money"])
        if MCP_SEND.search(action):
            verb = "email" if re.search(r"mail|gmail|outlook", tool_name, re.I) else "send"
            return Gate(verb, short(who), [f"{action} through {service}",
                                           f"to {who}" if who != action else "see the request"])
        if MCP_DELETE.search(action):
            return Gate("delete", short(who), [f"{action} through {service}"])
    return None


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import settings as settings_mod
    s = settings_mod.load()[0]
    g = classify("Bash", {"command": " ".join(sys.argv[1:])}, s, settings_mod.ROOT)
    if g is None:
        print("free to run")
    elif g.blocked:
        print(f"blocked: {g.blocked}")
    else:
        print(f"needs a signature: {g.phrase}")
        for d in g.details:
            print(f"  - {d}")
