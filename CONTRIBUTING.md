# Contributing

zipline has been tested on **one Linux machine, with a handful of made-up businesses and one
real one**. That's the honest limit of it, and it's the thing you can most easily help with.

## The most useful things you can send

**1. A session where it went in circles anyway.** The whole point is to stop the twentieth
version of the same email. If you got there regardless, the transcript is the most valuable
issue anyone could open: what you asked, where it should have stopped, and what it did
instead. **Take out names, prices, customer details and anything else about your business
first.** A transcript with `[customer]` and `[price]` in it is just as useful.

**2. `tools/setup.py` on a Mac, Windows or Fedora.** Only Ubuntu has been run for real. Paste
the whole output, and say whether the install command it printed actually worked.

**3. A draft that `tools/look.py` got wrong.** It said OK and the file was broken, or it flagged
something that was fine. Attach the draft if you can share it, or describe its shape if you
can't.

**4. A lesson that should be a rule.** If your `lessons.md` has the same thing in it twice,
that's a candidate for `CLAUDE.md` or for a check.

## Before you open a pull request

```
python3 tools/claimcheck.py                every claim zipline makes still holds
python3 tools/check_claims_can_fail.py     and every one of them can still go red
```

- **If you add or change a check, show it failing.** Run it once on something broken (red),
  then on the fixed version (green), and paste both in the pull request. A check that can't
  fail isn't a check, and it's worse than none because people trust it.
- **Say what you ran and what it showed.** "Should work" isn't a result.
- **Change one thing.** A pull request that fixes the loop rule and rewrites the setup tool
  can't be tested as either.
- **Editing the gate with its hooks on, keep it working at every step.** If an edit leaves
  `tools/gates.py` or `tools/hooks.py` broken (a call to a function you haven't added yet), the
  gate fails closed and refuses every editor action, including the one that would fix it. Add
  new functions before anything calls them. If you lock yourself out,
  `git checkout -- tools/gates.py` puts back the last working version.

## House rules, and why

**Nothing about a real business enters history.** No customer names, prices, email addresses,
logos or documents, in code, tests, examples or commit messages. The folders that hold a
business's own work (`brand/`, `drafts/`, `ready/`, `lessons.md`, `workalong.md`) are
gitignored for this reason. Don't un-ignore them, and use made-up businesses in examples.

**A rule earns its place with an incident.** The bar for adding to `CLAUDE.md` is not "this
seems sensible". It's "this went wrong, and nobody noticed until later." Say what happened in
the pull request. Rules added because they sound good are how instruction files bloat until
nobody follows any of them.

**Plain words in anything a user reads.** Say "assistant", "draft", "check". Not "AI-powered",
not "agent", no hype. The people this is for have been put off by text that sounds machine-made,
and the docs shouldn't sound that way either.

**No image generation.** zipline builds graphics from real fonts, layouts and shapes, so every
file can be opened and edited. Pull requests that add AI image generation won't be merged. That
isn't a judgement on the tools; it's a different project.
