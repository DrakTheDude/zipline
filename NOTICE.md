# Third-party notices

zipline is licensed Apache-2.0, see [LICENSE](LICENSE). That file is kept as the bare licence
text so automated tooling can identify it. Attribution lives here.

## Nothing is vendored

Everything in this repository was written for it. No third-party code, fonts or images are
copied in.

## Linked, not redistributed

- **[Small Business plugin](https://github.com/anthropics/knowledge-work-plugins/tree/main/small-business)**
  by Anthropic, Apache-2.0. `.claude/settings.json` points Claude Code at it; the plugin is
  fetched from its own repository and is not included here.

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
