// Turns the form's answers into workalong.md. Runs in the browser, and in Node for testing:
//   node -e "const f=require('./docs/form.js'); console.log(f.build({...}))"
// Nothing here talks to a server. The file is made on the person's own computer.

const LEVELS = {
  new: {
    name: "New to this",
    says: "The assistant stops after 2 tries at the same thing, agrees with you how to check " +
          "each piece of work before it starts, and explains as it goes. People who haven't been " +
          "burned yet don't notice the twentieth version until it's too late, so it stops early.",
  },
  burned: {
    name: "Been burned",
    says: "The assistant stops after 2 tries, and shows you the check result before it shows " +
          "you the draft. Trust comes back one checked result at a time.",
  },
  pattern: {
    name: "Know the pattern",
    says: "The assistant gets 4 tries, proposes its own checks, and gets on with it. You still " +
          "sign for anything that leaves the building.",
  },
};

const REACHES = ["email", "calendar", "accounts", "files", "shell", "remote-machines"];
// Same wording check as tools/settings.py: also-ask can only add.
const REMOVES = /^(no |not |skip |never ask|don't|dont |do not)/i;

// Where someone is with assistants, from what has happened to them, not a self-rating.
function levelFrom(a) {
  const burned = a.wrong === "once" || a.wrong === "stopped";
  if (!a.wrong) return "";
  if (burned && a.trusted === "yes") return "pattern";
  if (burned) return "burned";
  return "new";
}

// A settings line must stay one line: a newline in an answer would start a new setting.
function oneLine(s) {
  return String(s || "").replace(/[\r\n]+/g, " ").replace(/\s+/g, " ").trim();
}

function items(s) {
  return oneLine(s).split(",").map((x) => x.trim()).filter(Boolean);
}

function problems(a) {
  return items(a.alsoAsk).filter((x) => REMOVES.test(x))
    .map((x) => `"${x}" reads like removing something from the ask-first list. That list can ` +
                `only be added to: sending, prices and promises, deleting, spending and ` +
                `installing always need your OK.`);
}

function build(a) {
  const level = levelFrom(a);
  const network = a.computer === "managed" ? "strict" : "standard";
  const lines = ["---", "zipline: 1"];
  const business = oneLine(a.business);
  if (business) lines.push(`business: ${business}`);
  if (level) lines.push(`level: ${level}`);
  lines.push(`explain: ${{ no: "more", help: "normal", yes: "less" }[a.terminal] || "normal"}`);
  lines.push(`network: ${network}`);
  const allow = items(a.allow);
  if (network === "strict" && allow.length) lines.push(`allow: ${allow.join(", ")}`);
  lines.push(`users: ${a.users === "staff" ? "staff" : "just-me"}`);
  const reaches = (a.reaches || []).filter((r) => REACHES.includes(r));
  if (reaches.length) lines.push(`reaches: ${reaches.join(", ")}`);
  const alsoAsk = items(a.alsoAsk).filter((x) => !REMOVES.test(x));
  if (alsoAsk.length) lines.push(`also-ask: ${alsoAsk.join(", ")}`);
  lines.push("---", "", "# How we work here", "");
  const rules = String(a.rules || "").trim();
  lines.push(rules || "- (Your own rules go here, in your own words. For example: where prices " +
                      "come from, what the assistant should never touch, who checks what before " +
                      "it goes out.)");
  return lines.join("\n") + "\n";
}

if (typeof module !== "undefined") module.exports = { build, levelFrom, problems, LEVELS };
