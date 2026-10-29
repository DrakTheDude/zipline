---
name: interview
description: >
  Turns a goal like "more sales" or "more leads" into a brief: one piece of recurring work, what it
  costs the owner now in their own numbers, how they'd know a draft is right, and the checks that
  catch what went wrong before. Use when the owner says "interview me", "write my brief", "help me
  get specific", "what should I work on first", or states a goal with no number in it. Run it
  before any drafting skill, because the brief is what the drafts get judged against.
---

# Interview: from a wish to a brief

A goal with no number in it is a wish. A brief names one piece of recurring work, what it costs
now, and how you'd know it's done right. Most people can't write the last part on their own, and
that part is the reason to run this.

**Output:** `business/brief.md` and `business/claims.ini`, written only after the owner reads
them back and says they're theirs.

## Rules that do not bend

1. **Every number in the brief is the owner's, quoted.** Never estimate hours, prices or rates for
   them. If they don't know, the brief says "unknown" and names how they'll find out. A brief with
   an invented number is the confident, wrong output this exists to prevent. That includes
   numbers in the plan: if a next step needs a count ("time the next few"), ask the owner
   to pick it. Success criteria are in their words too; don't polish them into yours.
2. **One question at a time.** Wait for the answer.
3. **Ask about the last time, not "usually".** "Walk me through the last one" gets facts.
   "How do you usually..." gets the version they wish were true.
4. **Plain words.** Say "assistant", "draft", "check". Don't say AI, agent, model, prompt or LLM.
5. **Don't pitch, don't solve.** No suggestions until the read-back. This is listening.
6. **It's fine to stop short.** If no recurring work with a cost turns up, say so and write a
   "not ready yet" brief (see the end). Never force a brief.

## The questions

These are rungs, not a script. Skip any rung the owner has already answered, and stop climbing
once the brief is complete.

**1. What have you already tried, and what broke?**
Use it to open. It tells you how much they've done (don't ask them to rate themselves; people
rate themselves high and it tells you nothing). It surfaces the first incident (rung 6). And it
moves the conversation from wishes to events straight away.

**2. Find the work under the wish.**
If the goal is an outcome ("more customers", "grow sales"), don't argue with it. Go to the work
next to it:
- *"When a new customer or lead does come in, what do you have to do next?"*
- *"Think of the last one. What did you do between hearing from them and getting paid?"*

You're looking for **recurring work with a start and an end**: a call ends and a proposal has to
get written, a job is finished and an invoice has to go out. Often the wish is about getting
customers while the hours go into what happens after. Say that out loud if you hear it, and let
the owner pick which one to work on.

**3. What does it cost now?**
- *"How many of those did you do last month?"*
- *"How long did the last one take you, start to finish?"*
A range is fine. "No idea" is fine: write it down as unknown, and the first success criterion
becomes *"time the next few"*. Ask how many they'll time. Don't fill the gap with your own guess.

**4. What goes in, what comes out?**
*"What did you start from?"* (call notes, a transcript, photos, an email thread, a rate sheet)
*"What did you end up with?"* (a PDF, an email, an invoice). Ask where each one lives.

**5. How would you know a draft is right?**
*"If I handed you a draft of the last one, what would you check first?"*
Each answer is a success criterion. Push each one until you could check it without asking the
owner: "looks professional" becomes "uses our template, logo top left, no prices missing".

**6. What went wrong before, and how did you find out?**
*"Tell me about a time one of these went out wrong."* Then always ask: *"How did you find out?"*
- what went wrong → the claim's `why` (keep it in their words, it's the record of the incident)
- how they found out → what the check looks at
A thing that went wrong and was caught *late*, by a customer or by a lost deal, is the best
claim there is. If nothing has gone wrong yet, write no claim. Don't make one up.

**7. What must never go out without you?**
*"What's the one thing you'd be upset to find the assistant decided on its own?"*
Prices, dates, promises, anything sent to a customer are the usual answers. Each one becomes a
stop-and-ask rule. Sending is always on this list, whether or not they say it.

## The read-back

Read the brief back in their words, short:

> The work: **[task]**, which starts when **[trigger]** and ends with **[output]**.
> Now: **[their number]** a [week/month]. [Or: unknown, and you'll time the next [their count].]
> Done right means: **[criteria]**.
> Has gone wrong before: **[incident]**, found out when **[how]**.
> Never without you: **[gates]**.

Then ask: *"Is that yours? What's wrong with it?"* Fix what they correct. Write the files only
after a yes.

## business/brief.md

The read-back, plus where the inputs live, plus their own phrasing of the original wish (keep it;
it's how they'll recognise the brief later).

## business/claims.ini

One claim per real incident from rung 6. The header states what must be true; `why` is the
incident in their words:

```ini
[proposals: every proposal has a "not included" section]
why   = Spring job: the customer read "full renovation" as including the deck. We
        found out at final invoice and ate two days of labour.
prove = TODO: check the draft for a "Not included" heading
needs = a draft proposal exists in drafts/
```

- **`prove` may stay TODO.** Writing the check is a later step. The incident and what it looks
  at are what this conversation has to capture, because nobody can reconstruct them afterwards.
- **`needs` is for what the business doesn't have yet** (no rate sheet, no template). The claim
  shows as *unchecked*, not *failed*. Use it freely; a first run that's all red teaches people to
  ignore the report.
- Each claim needs a "how would we see this fail" answer. If there isn't one, it's a note, not a
  claim. Put it in the brief instead.

## When it isn't ready

If after rung 3 there's still no recurring work with a cost attached, don't push. Write a brief
that says so honestly: the wish in their words, the closest work you found, and **one thing to
notice this week** (*"jot down every time you write a quote and how long it took"*). Then offer
to run the interview again next week. A real "not yet" beats an invented brief.
