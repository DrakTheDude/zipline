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
- **The ask-first rules are instructions, not a lock.** They make the assistant stop and ask;
  they can't stop you from saying yes to something you shouldn't.

## 🔴 Don't attach your business files to a report

The natural thing to send with a bug is the draft that triggered it. If it holds real names,
prices or customer details, describe its shape instead, or replace the real values with
`[customer]`, `[price]` and so on before you attach it.
