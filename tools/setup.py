#!/usr/bin/env python3
"""Check this computer has what the workspace needs, and say how to get what's missing.

usage: python3 tools/setup.py             check only, and print the install command
       python3 tools/setup.py --install   run that install command (ask the person first)

It also creates the working folders (brand/, drafts/, ready/) if they're missing.
Exit code = the number of missing tools that drafts depend on.
"""
import os, platform, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = ["brand", "drafts", "ready"]

# name, how to detect it, needed for drafts?, what it's for, package per manager
TOOLS = [
    ("rsvg-convert", ["rsvg-convert"], True, "turn logos (SVG) into pictures",
     dict(apt="librsvg2-bin", dnf="librsvg2-tools", brew="librsvg")),
    ("pdftoppm", ["pdftoppm"], True, "turn PDFs into pictures",
     dict(apt="poppler-utils", dnf="poppler-utils", brew="poppler")),
    ("web page renderer", ["firefox", "weasyprint"], True, "turn emails and pages (HTML) into pictures",
     dict(apt="weasyprint", dnf="weasyprint", brew="weasyprint", winget="Mozilla.Firefox")),
    ("LibreOffice", ["soffice", "libreoffice"], False, "open and edit Word/Excel files, turn them into PDFs",
     dict(apt="libreoffice", dnf="libreoffice", brew="--cask libreoffice",
          winget="TheDocumentFoundation.LibreOffice")),
    ("Inkscape", ["inkscape"], False, "edit logos (SVG) by hand",
     dict(apt="inkscape", dnf="inkscape", brew="--cask inkscape", winget="Inkscape.Inkscape")),
]
FONTS = dict(apt="fonts-open-sans fonts-lato fonts-noto-core",
             dnf="open-sans-fonts lato-fonts google-noto-sans-fonts",
             brew="--cask font-open-sans,--cask font-lato")


def manager():
    system = platform.system()
    if system == "Darwin":
        return "brew" if shutil.which("brew") else None
    if system == "Windows":
        return "winget" if shutil.which("winget") else None
    for m in ("apt", "dnf"):
        if shutil.which(m + ("-get" if m == "apt" else "")) or shutil.which(m):
            return m
    return None


def install_commands(mgr, packages):
    if not packages:
        return []
    if mgr == "apt":
        return [["sudo", "apt-get", "install", "-y"] + packages]
    if mgr == "dnf":
        return [["sudo", "dnf", "install", "-y"] + packages]
    if mgr == "brew":  # casks and formulae are separate commands
        casks = [p.split()[-1] for p in packages if p.startswith("--cask")]
        formulae = [p for p in packages if not p.startswith("--cask")]
        cmds = [["brew", "install"] + formulae] if formulae else []
        return cmds + ([["brew", "install", "--cask"] + casks] if casks else [])
    if mgr == "winget":
        return [["winget", "install", "-e", "--id", p] for p in packages]
    return []


def fonts_present():
    if not shutil.which("fc-list"):
        return None  # can't tell (macOS/Windows without fontconfig)
    out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout.lower()
    return all(name in out for name in ("open sans", "lato"))


def main(install):
    for folder in FOLDERS:
        os.makedirs(os.path.join(ROOT, folder), exist_ok=True)
    mgr = manager()
    print(f"Computer: {platform.system()} · installer: {mgr or 'none found'}\n")
    missing, needed_missing, packages = [], 0, []
    for name, commands, needed, purpose, pkgs in TOOLS:
        found = next((c for c in commands if shutil.which(c)), None)
        mark = "ok     " if found else ("MISSING" if needed else "missing")
        print(f"  {mark} {name:<18} {purpose}")
        if not found:
            missing.append(name)
            needed_missing += needed
            pkg = pkgs.get(mgr)
            if pkg:
                packages += pkg.split() if not pkg.startswith("--cask") else [pkg]
            else:
                print(f"          no package known for {name} on this computer: install it by hand")
    fonts = fonts_present()
    print(f"  {'ok     ' if fonts else 'missing' if fonts is False else '?      '} {'open fonts':<18} "
          "free-to-use fonts for logos and documents")
    if fonts is False and FONTS.get(mgr):
        packages += FONTS[mgr].split() if mgr != "brew" else FONTS[mgr].split(",")
    print("\nFolders ready: " + ", ".join(f + "/" for f in FOLDERS))

    cmds = install_commands(mgr, packages)
    if not cmds:
        print("\nNothing to install." if not missing else "")
        return needed_missing
    print("\nTo install what's missing:")
    for cmd in cmds:
        print("  " + " ".join(cmd))
    if not install:
        print("\n(Run with --install to do it. The assistant asks you first.)")
        return needed_missing
    for cmd in cmds:
        print("\n$ " + " ".join(cmd))
        if subprocess.run(cmd).returncode != 0:
            print("That install failed. Nothing else was changed after it.")
            return max(needed_missing, 1)
    print("\nDone. Run tools/setup.py again to check.")
    return 0


if __name__ == "__main__":
    sys.exit(main("--install" in sys.argv[1:]))
