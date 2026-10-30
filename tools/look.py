#!/usr/bin/env python3
"""Turn a draft into a picture you can look at, and flag missing pieces.

usage: python3 tools/look.py <file> [<file> ...]

Writes PNGs to previews/ in the repo root and prints their paths. Open them (the Read tool shows
images) before telling anyone what a draft looks like.

- .svg          -> rsvg-convert
- .html / .htm  -> Firefox headless screenshot, or WeasyPrint if Firefox isn't there.
                   Also checks that every local file the page refers to (images, styles,
                   links) exists.
- .pdf          -> pdftoppm, first 3 pages
- .docx .doc .odt .xlsx .xls .ods .pptx .odp -> LibreOffice to PDF, then as a PDF
- .png / .jpg   -> already a picture, printed as is

Exit code = the number of problems found, so 0 means it rendered and nothing was missing.
Needs: librsvg2-bin, poppler-utils, and firefox or weasyprint. LibreOffice for office files.
python3 tools/setup.py checks all of these.
"""
import html.parser, pathlib, shutil, subprocess, sys, tempfile, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "previews"


class Refs(html.parser.HTMLParser):
    """Collects src/href values that point at local files."""
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("src", "href") and value:
                self.refs.append(value)


def local_refs(page):
    parser = Refs()
    parser.feed(page.read_text(errors="replace"))
    for ref in parser.refs:
        parsed = urllib.parse.urlparse(ref)
        if parsed.scheme in ("", "file") and not ref.startswith("#"):
            target = urllib.parse.unquote(parsed.path)
            if target:
                yield ref, (page.parent / target).resolve()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0, (r.stderr or r.stdout).strip()


def render_html(src, png):
    if shutil.which("firefox"):
        with tempfile.TemporaryDirectory() as profile:  # own profile: works while Firefox is open
            ok, err = run(["firefox", "--headless", "--no-remote", "--profile", profile,
                           "--screenshot", str(png), "--window-size=800,1400", src.as_uri()])
        if ok and png.exists():
            return [png], None
    if shutil.which("weasyprint") and shutil.which("pdftoppm"):
        pdf = png.with_suffix(".pdf")
        ok, err = run(["weasyprint", str(src), str(pdf)])
        if ok:
            return render_pdf(pdf, png)
        return [], err
    return [], "no HTML renderer: install firefox, or weasyprint + poppler-utils"


def render_pdf(src, png):
    if not shutil.which("pdftoppm"):
        return [], "pdftoppm missing: install poppler-utils"
    stem = png.with_suffix("")
    ok, err = run(["pdftoppm", "-png", "-r", "80", "-f", "1", "-l", "3", str(src), str(stem)])
    pages = sorted(OUT.glob(stem.name + "-*.png"))
    return (pages, None) if ok and pages else ([], err or "no pages rendered")


OFFICE = (".docx", ".doc", ".odt", ".rtf", ".xlsx", ".xls", ".ods", ".pptx", ".ppt", ".odp")


def render_office(src, png):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return [], "LibreOffice missing: run python3 tools/setup.py"
    with tempfile.TemporaryDirectory() as tmp:
        # own profile dir, so it works while LibreOffice is open on the desktop
        ok, err = run([soffice, f"-env:UserInstallation=file://{tmp}/profile", "--headless",
                       "--convert-to", "pdf", "--outdir", tmp, str(src)])
        pdf = pathlib.Path(tmp) / (src.stem + ".pdf")
        if not (ok and pdf.exists()):
            return [], err or "LibreOffice couldn't convert it"
        kept = OUT / (src.stem + ".pdf")
        shutil.copy(pdf, kept)
    return render_pdf(kept, png)


def look(path):
    src = pathlib.Path(path).resolve()
    problems = []
    if not src.exists():
        return [], [f"{path}: file not found"]
    png = OUT / (src.stem + ".png")
    kind = src.suffix.lower()
    if kind == ".svg":
        if not shutil.which("rsvg-convert"):
            return [], [f"{path}: rsvg-convert missing: install librsvg2-bin"]
        ok, err = run(["rsvg-convert", "-w", "800", str(src), "-o", str(png)])
        pics, err = ([png], None) if ok else ([], err)
    elif kind in (".html", ".htm"):
        for ref, target in local_refs(src):
            if not target.exists():
                problems.append(f"{path}: refers to {ref!r}, which doesn't exist")
        pics, err = render_html(src, png)
    elif kind == ".pdf":
        pics, err = render_pdf(src, png)
    elif kind in OFFICE:
        pics, err = render_office(src, png)
    elif kind in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        pics, err = [src], None
    else:
        pics, err = [], f"don't know how to show {kind or 'this'} files"
    if err:
        problems.append(f"{path}: {err}")
    return pics, problems


def main(paths):
    if not paths:
        print(__doc__.strip().splitlines()[2])
        return 2
    OUT.mkdir(exist_ok=True)
    problems = []
    for p in paths:
        pics, probs = look(p)
        for pic in pics:
            print(f"LOOK AT: {pic}")
        problems += probs
    for prob in problems:
        print(f"PROBLEM: {prob}")
    if not problems:
        print("OK: rendered, nothing missing. Now open the picture and check it.")
    return len(problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
