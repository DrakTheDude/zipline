# workalong.md: how this business works with the assistant

`workalong.md` sits in the top folder of your zipline copy. The form on the zipline page
writes it for you; you can also write or edit it by hand. It has two parts:

1. **Settings** between the `---` lines at the top. The tools read these.
2. **House rules** underneath, in plain words. You and the assistant both read these.

Run `python3 tools/settings.py` to see the settings in effect and check the file for
mistakes. Without a `workalong.md`, the defaults in the table below apply.

## Example

```markdown
---
zipline: 1
business: Rise & Crumb, a neighbourhood bakery
level: new
explain: more
network: standard
users: just-me
reaches: email, files
also-ask: anything with a price on it
---

# How we work here

- Prices come from the price list in brand/, never from memory.
- Every email to customers gets a test send to me first.
```

## Settings

| setting | values | default | what it does |
|---|---|---|---|
| `zipline` | `1` | `1` | which version of this format the file uses |
| `business` | one line | (none) | what the business is, so the assistant starts with the right picture |
| `level` | `new`, `burned`, `pattern` | (none) | where you are with assistants (see below). Sets `attempts` unless you set it yourself |
| `attempts` | 1 to 10 | from `level`, or 3 | how many goes at the same thing before the assistant stops and steps back |
| `explain` | `more`, `normal`, `less` | `normal` | how much the assistant explains what it's doing |
| `network` | `standard`, `strict` | `standard` | `standard`: known send actions need your signature. `strict`: anything that goes out over the network does, unless it's in `allow` |
| `allow` | comma-separated | (none) | with `strict`: addresses or commands that may go out without asking, like `archive.ubuntu.com` |
| `users` | `just-me`, `staff` | `just-me` | `staff` means other people use this too, so the house rules double as a staff policy |
| `reaches` | comma-separated | (none) | what the assistant can get at: `email`, `calendar`, `accounts`, `files`, `shell`, `remote-machines` |
| `also-ask` | comma-separated, your words | (none) | things that need your OK on top of the fixed list |

### Levels

| level | in plain words | attempts | how the assistant works |
|---|---|---|---|
| `new` | You're new to this, or it's been great so far | 2 | Agrees the check with you every time and explains each step. People here don't notice the twentieth version until it's too late, so it stops early. |
| `burned` | It's been confidently wrong on you, maybe you stopped using it for something | 2 | Shows you the check result before the draft. Trust comes back one checked result at a time. |
| `pattern` | You know the pattern: check first, try, look, decide | 4 | Proposes checks itself and gets on with it. |

### Always asks first

These five need your OK at every level, and `workalong.md` can't remove any of them:

- **send**: email, message, post, upload
- **promise**: setting or changing a price, a date, or a promise to a customer
- **delete**: deleting, overwriting or moving your files (except the assistant's own drafts
  and previews)
- **spend**: paying for or signing up to anything
- **install**: installing software on your computer

All but one are enforced: the action stops, the assistant shows you what it will do and a
short phrase, like `install gimp` or `email james`, and typing it lets that exact action run
once. "Yes" doesn't count. **promise** is the exception: a price inside a draft looks like any
other text, so the assistant is told to ask, and the draft can't go out without a send, which
is enforced. [safeguards.md](safeguards.md) has the full list of what stops.

`also-ask` adds to this list. Nothing takes away from it: the tools always start from these
five, whatever the file says, and a line like "don't ask before sending" is reported as a
mistake. What you add under `also-ask` is read by the assistant at the start of every session
and followed as an instruction; the tools can't recognise "anything with a price on it" in a
command, so it doesn't get a signature.

## When a house rule and a setting disagree

The stricter one wins for the job it's about. If `level: pattern` gives four attempts but a
house rule says "three tries per OS, then stop", fleet scripts stop at three and everything else
gets four.
