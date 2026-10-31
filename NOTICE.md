# Third-party notices

Copyright 2026 Petr Draxler.

zipline is licensed Apache-2.0, see [LICENSE](LICENSE). That file is kept as the bare licence
text so automated tooling can identify it. Attribution lives here.

## Nothing is vendored

Everything in this repository was written for it. No third-party code, fonts or images are
copied in. `tools/claimcheck.py` comes from the same author's
[stackchan-local-llm](https://github.com/DrakTheDude/stackchan-local-llm) and is used here
unchanged.

## Linked, not redistributed

- **[knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)** by
  Anthropic, Apache-2.0: small-business, engineering and operations. `.claude/settings.json`
  registers the marketplace and `tools/setup.py` turns on the ones a profile lists; Claude Code
  fetches them from their own repository. None is included here.

## Used on your computer, installed by you

`tools/setup.py` prints install commands for these, and `tools/look.py` calls them. Each is
installed through your own package manager, under its own licence, and none is bundled here:

| tool | used for | licence |
|---|---|---|
| librsvg (`rsvg-convert`) | SVG to PNG | LGPL-2.1+ |
| Poppler (`pdftoppm`, `pdftotext`) | PDF to PNG and text | GPL-2.0 or GPL-3.0 |
| WeasyPrint | HTML to PDF | BSD-3-Clause |
| Firefox | HTML to PNG | MPL-2.0 |
| LibreOffice | office files to PDF | MPL-2.0 |
| Inkscape | editing SVG by hand | GPL-2.0+ |
| Open Sans | font for drafts | Apache-2.0 (the version Ubuntu ships; newer releases are OFL) |
| Lato, Noto | fonts for drafts | SIL Open Font License 1.1 |

Calling these programs doesn't place zipline under their licences.
