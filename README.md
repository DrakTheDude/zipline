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

## What it looks like

You ask for a logo with a glossy 3D look. Before trying, the assistant says it can't make
that: it builds from fonts and shapes, so it offers a clean text logo, your own logo file, or
a designer. You pick the text logo. It makes `drafts/logo/logo-v1.svg`, looks at the picture
itself, then shows you.

Later you ask it to email the quote to James. It stops:

> This needs your OK before it runs. It sends an email to james@example.com with
> `ready/quote.pdf` attached. To go ahead, type: **email james**

You type `email james`, and that one email goes. The journal has a line for the request, your
signature and the send.

## Getting started

You need [Claude Code](https://claude.com/claude-code), through a Claude subscription or your
own API key, and Python 3.

1. **Set it up for your business** on the [zipline page](https://drakthedude.github.io/zipline/).
   A few questions about what's happened so far become a file called `workalong.md`: how many
   attempts before it steps back, how much it explains, and your own house rules. Your answers
   stay in your browser. You can skip this; sensible defaults apply.
2. **Get zipline:**
   ```
   git clone https://github.com/DrakTheDude/zipline.git
   ```
3. **Put `workalong.md` in the `zipline` folder**, then open it:
   ```
   cd zipline
   claude
   ```
4. **Say what you want to get done.** The first time, the assistant runs `tools/setup.py` to
   check your computer has what drafts need, and asks before installing anything.

## Where your work goes

Everything stays in the folder, on your computer, and out of git, so publishing or sharing
zipline never publishes your business.

| folder or file | what's in it |
|---|---|
| `brand/` | your logo, colours, fonts, price list: what every draft reuses |
| `drafts/<job>/` | work in progress, every version a new file (`menu-v1.html`, `menu-v2.html`) |
| `ready/` | what you've approved to go out |
| `previews/` | pictures the assistant made to check drafts (safe to delete) |
| `lessons.md` | what went wrong and what fixed it |
| `workalong.md` | your settings and house rules |
| `journal/` | what happened, one line each |

**zipline doesn't back these up.** They're kept out of git on purpose, so there's no history
of them anywhere else. Make sure your usual backup covers this folder.

## Keeping it up to date

```
cd zipline
git pull
```

Your work isn't touched: everything in the table above is yours and git leaves it alone. Put
your own rules in `workalong.md`, not in `CLAUDE.md` or the `tools/` folder. Those are
zipline's files, and changing them means an update can't come in cleanly (git will say so
rather than lose your change).

## How sure can you be

Some of this is enforced, and some is the assistant following instructions. The difference
matters, so here it is:

- **Enforced**, whatever the assistant decides: installing, sending, uploading, publishing,
  deleting or moving your files, changing `brand/` and your settings, writing outside the
  folder, connected-service actions that send, charge or delete, commits too big to review,
  and changes to GitHub. They stop until you sign. With a team, commits and pushes to main are
  refused outright, and so is any push while the project's claims fail.
  Your settings are put in front of the assistant at the start of every session. Attempts are
  counted and the limit announced. The journal can't be edited by the assistant.
- **Instructions**, which the assistant follows but nothing checks: agreeing the check first,
  saying what it can't make, resetting at the limit, asking before putting a price, date or
  promise in a draft, and your own house rules.

The safeguards read what the assistant is about to do. They catch an assistant that's
confident and wrong, not one hiding what it does. [docs/safeguards.md](docs/safeguards.md)
has every detail, and [SECURITY.md](SECURITY.md) the limits.

## Builds on

Anthropic's [knowledge-work plugins](https://github.com/anthropics/knowledge-work-plugins) for
Claude Code, chosen by profile: **small-business** (proposals, invoices, payroll prep and more)
for `business`, **engineering** (code review, debugging, testing, incident response) for
`code`, and engineering plus **operations** (runbooks, change requests, risk assessment) for
`infrastructure`. `tools/setup.py` turns on the profile's plugins for this folder; they load
the next time you start Claude Code here. zipline adds the working habits around them. A new
plugin is one line in a profile.

## Who it's for

People who already use an assistant for work and are comfortable opening a terminal, or the one
technical person a business relies on.

Tested on Ubuntu. macOS and Windows should work but haven't been tried yet; if you try,
[CONTRIBUTING.md](CONTRIBUTING.md) says what's most useful to send.

## More

- [docs/safeguards.md](docs/safeguards.md): what stops, how signing works, reading the journal
- [docs/workalong.md](docs/workalong.md): every setting in `workalong.md`, the profiles and the levels
- [profiles/](profiles/): the working rules for each kind of work: business, code, infrastructure
- [CLAUDE.md](CLAUDE.md): the working rules the assistant reads, in plain words
- [CONTRIBUTING.md](CONTRIBUTING.md): what helps most, and the checks to run
- [SECURITY.md](SECURITY.md): reporting a problem privately, and what this doesn't protect

## License

Apache-2.0. See [LICENSE](LICENSE). Third-party notes in [NOTICE.md](NOTICE.md).
