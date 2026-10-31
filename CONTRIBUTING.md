# Contributing

zipline has been tested on **one Ubuntu machine, with a handful of made-up businesses,
throwaway repositories and a few real sessions**. That's the honest limit of it, and it's the thing you can most easily help with.

## The most useful things you can send

**1. A session where it went in circles anyway.** The whole point is to stop the twentieth
version of the same email. If you got there regardless, the transcript is the most valuable
issue anyone could open: what you asked, where it should have stopped, and what it did
instead. **Take out names, prices, customer details and anything else about your business
first.** A transcript with `[customer]` and `[price]` in it is just as useful. The lines from
`journal/` for that session help too.

**2. An action that should have stopped and didn't.** Or one that stopped and shouldn't have.
[docs/safeguards.md](docs/safeguards.md) says what's meant to stop. If it's something that could
send, delete or spend without the person, report it privately (see [SECURITY.md](SECURITY.md)).

**3. `tools/setup.py` on a Mac, Windows or Fedora.** Only Ubuntu has been run for real. Paste
the whole output, and say whether the install command it printed actually worked.

**4. A draft that `tools/look.py` got wrong.** It said OK and the file was broken, or it flagged
something that was fine. Attach the draft if you can share it, or describe its shape if you
can't.

**5. A lesson that should be a rule.** If your `lessons.md` has the same thing in it twice,
that's a candidate for `CLAUDE.md` or for a check.

## Before you open a pull request

```
python3 tools/claimcheck.py                every claim zipline makes still holds
python3 tools/check_claims_can_fail.py     and every one of them can still go red
```

- **A new safeguard or rule needs a claim.** Add it to `claims.ini` with the incident in `why`,
  and a way to break it in `tools/check_claims_can_fail.py`. Change what stops? Update
  [docs/safeguards.md](docs/safeguards.md) in the same pull request.
- **If you add or change a check, show it failing.** Run it once on something broken (red),
  then on the fixed version (green), and paste both in the pull request. A check that can't
  fail isn't a check, and it's worse than none because people trust it.
- **Say what you ran and what it showed.** "Should work" isn't a result.
- **Change one thing.** A pull request that fixes the loop rule and rewrites the setup tool
  can't be tested as either.
- **Editing the gate with its hooks on, keep it working at every step.** If an edit leaves
  `tools/gates.py` or `tools/hooks.py` broken (a call to a function you haven't added yet), the
  gate fails closed and refuses every editor action, including the one that would fix it. Add
  new functions before anything calls them. If you lock yourself out, run
  `git checkout -- tools/gates.py` yourself, in a terminal: it puts back the last working
  version.
- **Every edit to the safeguards is signed.** `.claude/`, `tools/hooks.py`, `tools/gates.py`,
  `tools/settings.py`, `profiles/`, `CLAUDE.md` and `ZIPLINE.md` stop for `change safeguards`,
  one signature per edit. That's on purpose; batch your changes into fewer, bigger edits when
  working on them with an assistant.

## House rules, and why

**Nothing real enters history.** No customer names, prices, email addresses, logos or
documents, and no employer's code, hostnames, machine lists or keys, in code, tests, examples
or commit messages. Profiles and examples are written from scratch. The folders that hold a
business's own work (`brand/`, `drafts/`, `ready/`, `previews/`, `journal/`, `lessons.md`,
`workalong.md`) are gitignored for this reason. Don't un-ignore them, and use made-up businesses and machines in examples.

**A rule earns its place with an incident.** The bar for adding to `CLAUDE.md` or a profile is not "this
seems sensible". It's "this went wrong, and nobody noticed until later." Say what happened in
the pull request. Rules added because they sound good are how instruction files bloat until
nobody follows any of them.

**Plain words in anything a user reads.** Say "assistant", "draft", "check". Not "AI-powered",
not "agent", no hype. The people this is for have been put off by text that sounds machine-made,
and the docs shouldn't sound that way either.

**No image generation.** zipline builds graphics from real fonts, layouts and shapes, so every
file can be opened and edited. Pull requests that add AI image generation won't be merged. That
isn't a judgement on the tools; it's a different project.
