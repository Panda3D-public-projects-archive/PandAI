#!/usr/bin/env python3
"""Render COMMUNITY-NOTES.md into notes.html using the site shell.

A deliberately small Markdown subset -- exactly the constructs COMMUNITY-NOTES.md
uses -- so that the site stays buildable with a stock Python and no third-party
packages, matching the rest of tools/. Imported by build_site.py.
"""

import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "COMMUNITY-NOTES.md")
OUTPUT = os.path.join(ROOT, "notes.html")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Community field notes &middot; PandAI Archive</title>
<meta name="description" content="Bugs, workarounds and design notes for PandAI, gathered from fifteen years of Panda3D forum and Discord threads.">
<link rel="stylesheet" href="assets/css/site.css">
</head>
<body>
<header class="topbar">
  <a class="brand" href="index.html"><img src="assets/img/brand/PANDAILogo_new.png" alt=""><span>PandAI Archive</span></a>
  <nav class="edition">
    <a href="site/wiki/index.html">2016&ndash;2020 wiki</a>
    <a href="site/etc2010/index.html">2010 ETC site</a>
  </nav>
</header>
<main class="content notes">
{body}
</main>
<footer class="foot">
  <p>Compiled for the <a href="index.html">PandAI archive</a> from public Panda3D forum
  and Discord threads. Quotations belong to their authors.</p>
</footer>
</body>
</html>
"""


def slug(text):
    """Match GitHub's heading-anchor rule so the same table of contents works both
    here and in the rendered Markdown -- note it replaces each space individually,
    so "Status - should..." (em dash dropped) yields a double hyphen."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s", "-", text)


def inline(text):
    """Escape, then apply inline markup. Code spans are protected from the rest."""
    spans = []

    def stash(match):
        spans.append(match.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)

    # Backslash escapes ("A\*") must be hidden before the emphasis passes, or the
    # asterisk they protect breaks the very rule it was escaped to avoid.
    escapes = []

    def stash_escape(match):
        escapes.append(match.group(1))
        return "\x01%d\x01" % (len(escapes) - 1)

    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!])", stash_escape, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    # bare URLs that were not already turned into links
    text = re.sub(r"(?<!\")(?<!>)(https?://[^\s<>()]+)(?![^<]*</a>)", r'<a href="\1">\1</a>', text)
    text = re.sub(r"\x01(\d+)\x01", lambda m: escapes[int(m.group(1))], text)
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: "<code>%s</code>" % html.escape(spans[int(m.group(1))], quote=False),
                  text)


def render(markdown):
    out = []
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            out.append("<pre><code>%s</code></pre>"
                       % html.escape("\n".join(block), quote=False))
            i += 1
            continue

        if re.match(r"^#{1,4}\s", line):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            out.append('<h%d id="%s">%s</h%d>' % (level, slug(text), inline(text), level))
            i += 1
            continue

        if re.match(r"^---+\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # table: a header row followed by a |---|---| separator
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]

            head = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            table = ["<div class='tablewrap'><table class='filetable'><tr>"]
            table += ["<th>%s</th>" % inline(c) for c in head]
            table.append("</tr>")
            for r in rows:
                table.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            table.append("</table></div>")
            out.append("".join(table))
            continue

        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(quote).strip()))
            continue

        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i])
                                      or (items and lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r"^\s*[-*]\s+", lines[i]):
                    items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]).strip())
                else:
                    items[-1] += " " + lines[i].strip()   # continuation of the previous bullet
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(it) for it in items))
            continue

        if not line.strip():
            i += 1
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|```|>|\||---+\s*$|\s*[-*]\s)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(para)))

    return "\n".join(out)


def build():
    with open(SOURCE, encoding="utf-8") as fh:
        markdown = fh.read()
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(body=render(markdown)))
    print("rendered notes.html from COMMUNITY-NOTES.md")


if __name__ == "__main__":
    build()
