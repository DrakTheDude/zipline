# zipline

**From "this is amazing" to "this actually works", without the crash in between.**

Most people who start working with an assistant go through the same curve: a burst of
excitement, then a hard drop when it confidently gets things wrong, goes round in circles on
the twentieth version of an email, or can't make what they had in mind. Many give up there.
The ones who stick with it get to a steady, useful place on the other side.

zipline is a folder you open in Claude Code that takes you straight across. You steer, the
assistant drafts, and a few built-in habits keep the two of you from going in circles.

**Early days. It works and we're refining it.**

> **This is not an image generator.** It won't make AI art, so don't ask it to. Graphics are built
> the way a designer builds them: real fonts, real layouts, vector shapes (HTML/SVG → PDF). You can
> open, edit and reuse every file.

## What it does

- **Agrees the check before the draft.** What goes in, and how you'll both know it's right,
  before the first attempt. Most loops start with an input nobody looked at.
- **Says what it can't make, up front.** Not after the third disappointing try.
- **Looks before it shows.** Logos, emails, PDFs and office files are turned into pictures the
  assistant checks before telling you what it made. It also catches missing pieces, like an
  email pointing at a logo file that isn't there.
- **Stops going in circles.** It counts attempts. At the limit, or when you're repeating
  yourself, it stops, says back what it thinks the goal is, and asks the one question that
  would change the approach.
- **Drafts, never sends.** Sending, deleting your files, spending money and installing software
  stop until you sign: the assistant shows you exactly what will happen, and you type a short
  phrase like `email james` to let that one action run once. "Yes" doesn't count.
- **Keeps a journal.** One plain line per thing that happened, in `journal/`, written by the
  safeguards, not the assistant.
- **Remembers what went wrong.** Lessons go in `lessons.md`, and the assistant reads them before
  similar work.

## Getting started

You need [Claude Code](https://claude.com/claude-code), through a Claude subscription or your
own API key.

```
git clone https://github.com/DrakTheDude/zipline.git
cd zipline
claude
```

Then say what you want to get done. The first time, the assistant runs `tools/setup.py` to
check your computer has what drafts need, and asks before installing anything.

Your work stays on your computer: `brand/` for your logo and colours, `drafts/` for work in
progress (every version kept), `ready/` for what you've approved. None of it is uploaded.

## Builds on

The [Small Business plugin](https://github.com/anthropics/knowledge-work-plugins/tree/main/small-business)
for Claude Code (proposals, invoices, payroll prep and more) is turned on when you open this
folder. zipline adds the working habits around it.

## Who it's for

People who already use an assistant for work and are comfortable opening a terminal, or the one
technical person a business relies on.

## License

Apache-2.0. See [LICENSE](LICENSE).
