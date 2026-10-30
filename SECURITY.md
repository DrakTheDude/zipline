# Security and privacy reporting

zipline runs on a business owner's own computer, next to their customer lists, prices and
documents, and its whole promise is that **the assistant drafts and the person decides**. So
two kinds of defect are the most serious this project can have:

1. **Business data leaving the computer** when nobody asked it to.
2. **An ask-first rule that can be talked past.** If the assistant sends, deletes, spends,
   installs or sets a price without the person's OK, that's a security bug here, not a
   behaviour quirk.

## How to report

**Please don't open a public issue for either of those.** Use:

- GitHub's **[private vulnerability reporting](https://github.com/DrakTheDude/zipline/security/advisories/new)**
  on this repository, or
- **petrdraxler@gmail.com**

This is maintained by one person, so there's no response time guarantee. A few days is
realistic. If it's affecting real businesses right now, say so in the subject line.

## In scope

- Anything in this repository that sends a business's files, drafts or customer details
  anywhere, on any path
- The gitignore failing to keep `brand/`, `drafts/`, `ready/`, `lessons.md` or `workalong.md`
  out of a commit
- A way to get the assistant past the ask-first list in `CLAUDE.md` (sending, prices and
  promises, deleting files, spending money, installing software) using this repository's
  instructions as written
- `tools/setup.py` installing anything without `--install`
- `tools/look.py` reporting OK on a draft that refers to a file that doesn't exist

## Out of scope

- **Claude Code and the model itself.** Report those to Anthropic.
- **The Small Business plugin.** It's linked, not part of this repository. Report to
  [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins).
- **Things the person approved.** If they said yes to sending it, it was sent on purpose.

## What this project doesn't protect you from

Be clear about this before trusting it with anything sensitive:

- **Your conversations go to the assistant's service.** That's how Claude Code works, with your
  subscription or API key. zipline keeps your files on your computer. It doesn't keep what you
  type or show the assistant on your computer.
- **Previews load what a draft points to.** `tools/look.py` opens HTML drafts in a browser. If
  a draft links to an image on the web, the preview fetches it, like any email client would.
- **Signatures stop what the gate can recognise, not everything.** `tools/gates.py` reads
  commands and tool names: package installs, deletes, moves, mail, uploads, pushes, connector
  actions that send, charge or delete, files written outside this folder (by the editor or by
  shell commands such as `cp`, `tee`, `sed -i`, redirects and `git apply`, following `cd`), and
  in strict mode anything that reaches an address not on your list. An action disguised as
  something else (a script that quietly sends email, or writes a file without saying so) gets
  past it. It guards against an assistant that is confident and wrong, not one trying to hide
  what it does.
- **The journal and `.zipline/` are protected by the same reading of commands.** Direct writes,
  redirects and any non-read-only command that names them are refused. A deliberately evasive
  command could still reach them. The rule errs the other way too: a shell command that merely
  mentions them in text (say, a script editing these docs) is refused, so edit such files with
  the editor, which is judged by path.
- **Prices, dates and promises inside a draft aren't detected.** They're caught when the draft
  is sent, which is gated.
- **A signature can't stop you from approving something you shouldn't.** It makes sure you were
  shown the specifics first.
- **Only what you type can sign.** Claude Code also passes its own messages through the same
  place (a subagent's finished-task report, for one), and those are ignored, even if they
  contain the exact phrase. This is matched on the wrappers Claude Code uses today; a new kind
  of system message in a future version would need adding. Gated actions inside a subagent are
  stopped the same as in the main session (tested).

## 🔴 Don't attach your business files to a report

The natural thing to send with a bug is the draft that triggered it. If it holds real names,
prices or customer details, describe its shape instead, or replace the real values with
`[customer]`, `[price]` and so on before you attach it.
