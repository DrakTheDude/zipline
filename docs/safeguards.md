# The safeguards: what stops, how signing works, and what the journal says

zipline gives the assistant working habits in `CLAUDE.md`, and backs the important ones with
safeguards that run whether the assistant remembers them or not. This page is the detail:
what each safeguard does, what you'll see, and where it stops.

Claude Code runs `tools/hooks.py` at four points: when a session starts, when you send a
message, before the assistant uses a tool, and after it saves a file. You don't call it, and
neither does the assistant. The switches are in `.claude/settings.json`.

## When a session starts

The assistant is handed your settings from `workalong.md` and your house rules, before it
does anything else. Without that file, the defaults apply and it's told so.

This exists because of a real session: with a `workalong.md` that allowed downloads from
only two addresses, the assistant was asked to install an image editor, never opened the
file, and installed it from somewhere else with administrator rights. `CLAUDE.md` said "read
it first". Nothing made it.

## Actions that stop until you sign

Before the assistant runs a command or uses a tool, the gate (`tools/gates.py`) reads what
it's about to do. If it's one of these, it doesn't run:

| what | example phrase | what you're shown |
|---|---|---|
| installing or removing software | `install gimp` | where it comes from, whether it needs administrator rights, whether it updates itself |
| sending email | `email james` | who it goes to |
| uploading, posting, sending data to a website | `send example.com`, `upload server1` | where it goes |
| publishing code | `push origin` | where it's published |
| deleting or moving your files | `delete menu.pdf` | which files; that it can't be undone from here |
| changing your files in `brand/`, `workalong.md`, `lessons.md` | `overwrite logo.svg` | which file |
| putting a draft in `ready/` | `approve quote.pdf` | which draft |
| writing a file outside the zipline folder | `write notes.txt` | the full path |
| a connected service (email, payments, calendar) that sends, charges or deletes | `email james`, `charge alex` | the service, the action and who it's for |
| with `network: strict`, reaching anything not on your `allow` list | `connect example.org` | the address |
| a commit with more files than `commit-files` (default 15) | `commit 23 files` | how many, and the suggestion to split it |
| changing GitHub with `gh`: merging, repo settings, releases, review rules | `change github` | the command |

The assistant tells you the specifics in plain words, and the phrase. **To let it go ahead,
type the phrase.** That lets exactly that action run, once. Then it stops again next time.

- **"Yes" doesn't count.** Neither does "ok, go ahead". Typing the action's name means you read
  which action it is.
- **Close isn't enough, and you're told.** "install gimp please" gets a reply that it isn't the
  phrase, so you don't walk away thinking you signed.
- **The phrase covers the command you were shown, not a similar one.** If the assistant
  changes the command after you sign (a different source, a different file), that's a new
  request with new specifics. The assistant rewording its own description of the command
  doesn't count as a change.
- **Requests run out.** You have 30 minutes to sign a request, and once signed it has to run
  within 5 minutes. After that you're told it ran out, and the assistant asks again.
- **Only what you type can sign.** Claude Code passes some of its own messages through the same
  place (a helper task's finished report, for one). Those are ignored, even if they contain
  the exact phrase. Gated actions inside such helper tasks stop the same way.
- **A request the assistant dropped doesn't take your next "yes".** "Yes" and near misses
  only answer a request raised since your last message.

Some things are never allowed, signed or not: changing `journal/` or `.zipline/`, where the
safeguards keep their records.

### Git rules

`team` in `workalong.md` says how many people review the work.

| | `solo` (default) | `pair` | `team` |
|---|---|---|---|
| commit on main | allowed | refused: make a branch named for the piece of work | refused |
| push to main | signed (`push origin`) | refused: push the branch, open a pull request | refused |
| push a branch | signed | signed | signed |
| reviews before merging | none | 1 | 2 |

Refused means no signature can allow it; a branch costs nothing, and a signature here would
become a habit. Reviews are enforced by GitHub, not here: `tools/setup.py` prints the command
that sets the rule on the repository (signed as `change github`; private repositories need a
paid GitHub plan for it). GitHub won't let you approve your own pull request, which is why
`solo` pushes directly.

At every team size, if the repository has a `claims.ini`, a push is refused while any claim
fails, and you're told which. If the claims take more than 45 seconds, the push asks for a
signature and says it's unvalidated.

The rules read the branch at the moment the command is checked: `git switch -c fix && git
commit` in one command is judged on the branch you were on. Run them as two commands.

### What doesn't stop

Ordinary work: drafts, previews, reading files, running checks. Deleting files inside
`drafts/` and `previews/` is free too, because those are the assistant's scratch space and
every version is a separate file. A gate on everything would teach you to sign without
reading, which is the reflex this exists to break.

### Prices, dates, promises, and your own additions

These are on the always-ask list, but **no safeguard can see them.** A price inside a draft
looks like any other text. The assistant is told to ask, and the draft can't leave the
computer without a send, which is gated. The same goes for anything you add under
`also-ask` in `workalong.md` and for your house rules: the assistant reads them at the start
of every session and is told to follow them, but they're instructions, not locks.

## Counting attempts

Every new version of a draft is a new file, `drafts/<job>/<name>-v1.html`, `-v2`, and so on.
After each one is saved, the assistant is told which attempt it was out of your limit (from
`level` or `attempts`, otherwise 3). On the last one it's told this is the limit; past it,
that it has gone over, and it goes in the journal.

At the limit the assistant doesn't try again. It resets: stops, says back the goal and what it
assumed, asks you the one question that would change the approach, and proposes a different
route. You can say "keep going"; that's your call, and it's written down.

## Noticing when you're repeating yourself

When you say the result still isn't right ("still wrong", "that's not it", "try again",
"didn't work") twice within your last four messages, or send one nearly the same as an
earlier one, the assistant is told you may be going round in circles and resets. Then it
starts counting afresh.

Only short messages count, and only your own words: a correction is usually a line, and a
long message that says "it's the same problem" is usually someone explaining. Pasted text is
someone else's words. Both rules came from false alarms in a real session. The trade-off is
that a long, frustrated message on its own won't trigger it; you can always just say "let's
step back".

## The journal

`journal/2026-10.md`, one file per month, one line per thing that happened. Only the
safeguards write it. The assistant can read it to you but can't change it.

```
2026-10-30 03:27  asked       overwrite claude.md · changes /home/you/notes/CLAUDE.md, outside this folder
2026-10-30 03:28  signed      "overwrite claude.md"
2026-10-30 03:28  used        overwrite claude.md
2026-10-30 03:28  done        overwrite claude.md
```

| line | means |
|---|---|
| `session` | a session started; the settings it started with |
| `attempt`, `limit`, `over-limit` | a new version of a draft; the last allowed one; one past the limit |
| `in-place` | a draft version was changed instead of saved as a new one |
| `repeating` | your message looked like the same request again |
| `asked` | an action was stopped, with the specifics you were shown |
| `signed`, `not-signed` | you typed the phrase; or typed something that wasn't it |
| `used`, `done` | the signed action ran; and finished |
| `expired` | a request or signature ran out of time unused |
| `refused` | something no signature can allow (changing the journal) |
| `problem` | a safeguard itself failed |

Ask the assistant "what's in the journal this week?" or open the file yourself. It stays on
your computer and out of git, like the rest of your business's files.

## If a safeguard breaks

A safeguard that crashes doesn't stop your session: the error goes in the journal as a
`problem` line and the assistant is told to tell you. The exception is the gate: if it can't
decide, the action doesn't run. A lock that opens when it breaks isn't a lock.

## What they don't do

They read commands and tool names. They catch an assistant that is confident and wrong, not
one trying to hide what it does: a script that quietly sends email from inside, without
saying so on the command line, gets past. [SECURITY.md](../SECURITY.md) lists the limits in
full.

## Turning them off

Remove the `hooks` section from `.claude/settings.json`. The working habits in `CLAUDE.md` still
apply, but nothing checks them.

## How they're checked

Each safeguard has a claim in `claims.ini` with the incident that made it necessary. One
command proves them all still hold, and another proves each one can still fail when its
safeguard is broken:

```
python3 tools/claimcheck.py
python3 tools/check_claims_can_fail.py
```
