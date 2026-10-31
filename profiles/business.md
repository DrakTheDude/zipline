---
profile: business
for: running a business: emails, quotes, logos, menus, spreadsheets, documents
folders: brand, drafts, ready
tools: rsvg-convert, pdftoppm, web page renderer, LibreOffice, Inkscape, open fonts
---

## Where things go

Keep everything in this folder, in these places, so the person always knows where to look:

| what | where |
|---|---|
| their logo, colours, fonts, anything every draft reuses | `brand/` |
| a piece of work in progress | `drafts/<short-name>/`, one folder per job |
| each new version of a draft | a new file: `<name>-v1.html`, `<name>-v2.html`, ... Never overwrite the last one; "the earlier one was better" is common. |
| finished and approved by the person, ready for them to send | `ready/`, only after their OK |
| preview pictures | `previews/` (made by `tools/look.py`, safe to delete) |
| what went wrong and what worked | `lessons.md` |

Drafts refer to `brand/` files rather than copying them. All of this stays on this computer:
it's left out of git, so nothing about the business gets published by accident. Each new
`-vN` file in `drafts/<job>/` is an attempt, and the safeguards count them.

## What it will look like

If what they're picturing is something you can't make, say so *before* the first attempt, not
after the second. The common one: you don't generate images. Glossy, 3D, painterly or
photo-real pictures like the AI art people see online are out of reach. What you can make is
built from real fonts, layouts and simple shapes. Say what that will look like, and offer the
honest options: a clean text or shape design from you, their own logo file, or a designer.
Don't try to fake the look with shapes; that's the first attempt in a loop.

## Look before you show

You can't judge a logo, an email, a PDF or a Word file from its code. Before you tell the
person what a visual draft looks like, run:

```
python3 tools/look.py <file>
```

then open the PNG it prints and check it against what you're about to claim. It also flags
any file the draft refers to that doesn't exist (an image, an attachment). Any `PROBLEM` line
means the draft isn't ready, whatever it looks like.

If the tool can't run, say plainly that you haven't seen the result. And remember it's a
browser's view: Gmail and Outlook can show an email differently, so the person still sends
themselves a test before the real send.
