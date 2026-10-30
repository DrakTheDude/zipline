---
zipline: 1
business: IT for a small company: a mixed fleet of Windows and Ubuntu machines (example)
level: pattern
explain: less
network: strict
allow: archive.ubuntu.com, security.ubuntu.com, github.com
users: staff
reaches: files, shell, remote-machines
also-ask: anything that runs on more than one machine, changing a firewall or a user account
---

# How we work here

- **Nothing reaches the fleet untested.** A script for the fleet is a draft until it has run
  in a fresh virtual machine for each OS it targets and passed its checks (exit codes, the
  installed version, the service running). Three tries per OS, then stop and report what
  failed. I deploy the version that passed.
- **Write the check before the script.** What does "installed" mean on each OS? Agree that
  first; most failed deploys were scripts that "worked" against a check nobody wrote down.
- **If each new app needs its own pile of fixes, stop.** That means we're patching around the
  problem instead of solving it. Step back and change the approach.
- The list of machines that must never be touched is kept on my computer, not here. Ask
  before acting on any machine you haven't been told is safe.
- Staff read these rules too. If something here is unclear to them, it's unclear.
