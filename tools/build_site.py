#!/usr/bin/env python3
"""Rebuild the static site under site/ from the verbatim captures in archive/raw/.

The two source sites were laid out very differently:

  * archive/raw/etc-cmu/      the original 2010 ETC project site (hand-written XHTML,
                              content lives in <div id="mainContent">)
  * archive/raw/google-sites/ the 2016-2020 Google Sites wiki (content lives in
                              <div id="sites-canvas-main-content">)

Both are reduced to their content fragment, re-pointed at local assets/downloads,
and wrapped in a shared shell. Run from the repo root: python3 tools/build_site.py
"""

import html
import json
import os
import re
import shutil
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CMU = os.path.join(ROOT, "archive", "raw", "etc-cmu")
RAW_SITES = os.path.join(ROOT, "archive", "raw", "google-sites")
OUT_CMU = os.path.join(ROOT, "site", "etc2010")
OUT_WIKI = os.path.join(ROOT, "site", "wiki")

WAYBACK_CMU = "https://web.archive.org/web/20170123102252/https://etc.cmu.edu/projects/pandai/index.html"
WAYBACK_SITES = "https://web.archive.org/web/20201022234250/https://sites.google.com/site/etcpandai/"


# --------------------------------------------------------------------------
# content extraction
# --------------------------------------------------------------------------

class DivExtractor(HTMLParser):
    """Capture the inner HTML of the first <div>/<td> carrying a given id."""

    def __init__(self, target_id):
        super().__init__(convert_charrefs=False)
        self.target_id = target_id
        self.depth = 0
        self.capturing = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if not self.capturing and d.get("id") == self.target_id:
            self.capturing = True
            self.depth = 1
            return
        if self.capturing:
            if tag == "div":
                self.depth += 1
            if tag not in ("br", "hr", "img", "meta", "link", "input"):
                self.parts.append(self.get_starttag_text())
            else:
                self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if not self.capturing:
            return
        if tag == "div":
            self.depth -= 1
            if self.depth == 0:
                self.capturing = False
                return
        self.parts.append("</%s>" % tag)

    def handle_startendtag(self, tag, attrs):
        if self.capturing:
            self.parts.append(self.get_starttag_text())

    def handle_data(self, data):
        if self.capturing:
            self.parts.append(data)

    def handle_entityref(self, name):
        if self.capturing:
            self.parts.append("&%s;" % name)

    def handle_charref(self, name):
        if self.capturing:
            self.parts.append("&#%s;" % name)

    def handle_comment(self, data):
        if self.capturing:
            self.parts.append("<!--%s-->" % data)

    def result(self):
        return "".join(self.parts)


def extract(path, target_id):
    with open(path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()
    parser = DivExtractor(target_id)
    parser.feed(source)
    title = re.search(r"<title>(.*?)</title>", source, re.S | re.I)
    title = html.unescape(title.group(1)).strip() if title else ""
    title = re.sub(r"\s*-\s*PandAI$", "", title).strip() or "PandAI"
    return title, parser.result()


# --------------------------------------------------------------------------
# download link resolution
# --------------------------------------------------------------------------

def build_download_index():
    """Map each archived attachment filename to where its bytes now live."""
    index = {}
    for sub in ("HistoricalVersions", "HistoricalVersions/samples",
                "HistoricalVersions/etc-cmu-2010-2012"):
        directory = os.path.join(ROOT, sub)
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, name)):
                index.setdefault(name, "%s/%s" % (sub, name))
    # The four byte-identical duplicates were not re-copied under etc-cmu-2010-2012;
    # CMU-era links for them resolve to the single retained copy.
    return index


DOWNLOADS = build_download_index()

TEAM_PHOTOS = {
    "DeepakMuraliChandrasekaran.jpg": "DeepakMuraliChandrasekaran.jpg",
    "JohnKolencheryl.jpg": "JohnKolencheryl.jpg",
    "KyleDolan.jpg": "KyleDolan.jpg",
    "mikechristel.jpg": "mikechristel.jpg",
    "ruthcomley.jpg": "ruthcomley.jpg",
    "SrinavinNair.jpg": "SrinavinNair.jpg",
    "Jy-Huey%28Grace%29Lin.jpg": "Jy-Huey-Grace-Lin.jpg",
    "Jy-Huey(Grace)Lin.jpg": "Jy-Huey-Grace-Lin.jpg",
}

RESEARCH_IMAGES = {
    "Research_clip_image001.gif": "Research_clip_image001.gif",
    "Research_clip_image001.jpg": "Research_clip_image001.jpg",
    "Research_clip_image002.gif": "Research_clip_image002.gif",
    "Research_clip_image003.gif": "Research_clip_image003.gif",
    "view%20angle.jpg": "view-angle.jpg",
    "view angle.jpg": "view-angle.jpg",
}


def wiki_slug(site_path):
    """/site/etcpandai/documentation/steering-behaviors/seek -> seek.html"""
    rel = site_path.replace("/site/etcpandai", "").strip("/")
    if not rel or rel == "home":
        return "index.html"
    return rel.replace("/", "__") + ".html"


def rewrite_common(markup, prefix):
    """Rewrite asset + attachment references that appear in both sites."""
    # team photos (Google Sites serves them through /_/rsrc/<ts>/... with size args)
    def team_sub(match):
        url = match.group(0)
        for archived, local in TEAM_PHOTOS.items():
            if archived in url:
                return 'src="%sassets/img/team/%s"' % (prefix, local)
        return url

    # the 2010 site uses "Team/x.jpg", the wiki "/_/rsrc/<ts>/what-is-pandai/team/x.jpg"
    markup = re.sub(r'src="[^"]*\bteam/[^"]*"', team_sub, markup, flags=re.I)

    def research_sub(match):
        url = match.group(0)
        for archived, local in RESEARCH_IMAGES.items():
            if archived in url:
                return 'src="%sassets/img/research/%s"' % (prefix, local)
        return url

    markup = re.sub(r'src="[^"]*\b(?:Research|research)/[^"]*"', research_sub, markup)

    # "view the full image" links that point back at the live Google Sites host
    def photo_link_sub(match):
        url = match.group(0)
        for archived, local in TEAM_PHOTOS.items():
            if archived in url:
                return 'href="%sassets/img/team/%s"' % (prefix, local)
        return url

    markup = re.sub(r'href="[^"]*\bteam/[^"]*\.jpg[^"]*"', photo_link_sub, markup, flags=re.I)

    # attachment links -> the copies retained in this repo
    def download_sub(match):
        url = html.unescape(match.group(1))
        name = url.split("?")[0].rstrip("/").split("/")[-1]
        target = DOWNLOADS.get(name)
        if target:
            return 'href="%s%s"' % (prefix, target)
        return match.group(0)

    markup = re.sub(r'href="([^"]*\.(?:zip|docx|rar))[^"]*"', download_sub, markup)

    # protocol-relative / http YouTube embeds -> https
    markup = markup.replace('src="http://www.youtube.com', 'src="https://www.youtube.com')

    # The 2010 site shipped six team e-mail links missing their "mailto:" scheme, so
    # they resolved against the page directory ("../Templates/name@andrew.cmu.edu").
    # The addresses were always plain visible text; only the href was broken.
    markup = re.sub(
        r'href="(?:\.\./|https?://www\.etc\.cmu\.edu/projects/)Templates/([^"@]+@[^"]+)"',
        r'href="mailto:\1"', markup)
    return markup


def rewrite_wiki(markup):
    markup = rewrite_common(markup, "../../")

    def link_sub(match):
        target = html.unescape(match.group(1))
        if re.search(r"\.(zip|docx|rar)", target):
            return match.group(0)
        if "/_/" in target or "/system/" in target:
            return match.group(0)
        return 'href="%s"' % wiki_slug(target)

    markup = re.sub(r'href="(?:https?://sites\.google\.com)?(/site/etcpandai[^"]*)"',
                    link_sub, markup)
    # cross-links to the old ETC site now resolve to the 2010 mirror
    markup = markup.replace('href="http://www.etc.cmu.edu/projects/pandai/index.html"',
                            'href="../etc2010/index.html"')
    return markup


FLASH_OBJECT = re.compile(r"<object\b.*?</object>", re.S | re.I)
YOUTUBE_ID = re.compile(r"youtube\.com/v/([A-Za-z0-9_-]{6,})")


def flash_to_iframe(markup):
    """The 2010 site embedded its demo reels with the Flash <object>/<embed> player.

    No current browser can play those, so each block is swapped for the modern
    iframe player carrying the same video id. Blocks without a recognisable id are
    left alone rather than silently dropped.
    """
    def sub(match):
        block = match.group(0)
        found = YOUTUBE_ID.search(block)
        if not found:
            return block
        return (
            '<div class="videoframe"><iframe width="660" height="371" '
            'src="https://www.youtube.com/embed/%s" title="PandAI demo video" '
            'frameborder="0" allowfullscreen></iframe></div>' % found.group(1)
        )

    return FLASH_OBJECT.sub(sub, markup)


def rewrite_cmu(markup):
    markup = flash_to_iframe(markup)
    markup = rewrite_common(markup, "../../")
    markup = re.sub(r'src="About/PANDAILogo_new\.png"',
                    'src="../../assets/img/brand/PANDAILogo_new.png"', markup)
    markup = re.sub(r'src="About/([^"]+)"',
                    r'src="../../assets/img/brand/\1"', markup)
    return markup


# --------------------------------------------------------------------------
# page shell
# --------------------------------------------------------------------------

WIKI_NAV = [
    ("index.html", "Home"),
    ("what-is-pandai.html", "What is PandAI"),
    ("documentation.html", "Documentation"),
    ("tutorials.html", "Tutorials"),
    ("examples.html", "Examples"),
    ("download.html", "Download"),
]

CMU_NAV = [
    ("index.html", "Home"),
    ("Team.html", "Team"),
    ("Research.html", "Research"),
    ("Community.html", "Community"),
    ("Gallery.html", "Gallery"),
    ("Pathfinding.html", "Pathfinding"),
    ("Download.html", "Download"),
    ("aitypes.html", "AI Types"),
]

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; PandAI Archive</title>
<link rel="stylesheet" href="../../assets/css/site.css">
</head>
<!-- rebuilt by tools/build_site.py -->
<body>
<header class="topbar">
  <a class="brand" href="../../index.html">
    <img src="../../assets/img/brand/PANDAILogo_new.png" alt="">
    <span>PandAI Archive</span>
  </a>
  <nav class="edition">
    <a href="../wiki/index.html"{wiki_active}>2016&ndash;2020 wiki</a>
    <a href="../etc2010/index.html"{cmu_active}>2010 ETC site</a>
  </nav>
</header>
<div class="banner">
  Archived copy of a site that is no longer online &mdash;
  <a href="{wayback}">original snapshot on the Wayback Machine</a>.
</div>
<nav class="sectionnav">{nav}</nav>
<main class="content{extra_class}">
<h1>{title}</h1>
{body}
</main>
<footer class="foot">
  <p>PandAI was built at the Carnegie Mellon Entertainment Technology Center. This is an
  unofficial preservation mirror; all content belongs to its original authors.</p>
</footer>
</body>
</html>
"""


def render(title, body, nav_items, current, wayback, edition, extra_class=""):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="on"' if href == current else "", label)
        for href, label in nav_items
    )
    return SHELL.format(
        title=html.escape(title),
        body=body,
        nav=nav,
        wayback=wayback,
        extra_class=extra_class,
        wiki_active=' class="on"' if edition == "wiki" else "",
        cmu_active=' class="on"' if edition == "cmu" else "",
    )


VIDEO_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo videos &middot; PandAI Archive</title>
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
<main class="content">
<h1>Demo videos</h1>
<p>Every demo reel the two sites embedded. The videos are hosted on YouTube and are not
mirrored in this repository &mdash; this index exists so that the identifiers, titles and
uploaders survive even if the embeds stop resolving. That metadata is also kept as
<code>archive/videos.json</code>. All {count} were confirmed playing when this page was
generated.</p>
<div class="tablewrap">
<table class="filetable">
<tr><th>Video</th><th>Uploaded by</th><th>Appears on</th></tr>
{rows}
</table>
</div>
</main>
<footer class="foot"><p>Part of the <a href="index.html">PandAI archive</a>.</p></footer>
</body>
</html>
"""


def build_video_index():
    """List every embedded demo video with a direct link.

    The videos themselves stay on YouTube; only the identifiers are preserved here.
    """
    videos = {}

    for name in sorted(os.listdir(RAW_SITES)):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(RAW_SITES, name), encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        page = re.sub(r"\s*-\s*PandAI$", "",
                      html.unescape(re.search(r"<title>(.*?)</title>", source, re.S).group(1)).strip())
        # a Google Sites embed carries its caption in the <h4> just above the iframe
        for block in re.findall(r'<h4 class="sites-embed-title">(.*?)</h4>.*?youtube\.com/embed/([A-Za-z0-9_-]+)',
                                source, re.S):
            caption = html.unescape(re.sub(r"<[^>]+>", "", block[0])).strip()
            videos.setdefault(block[1], (caption, set()))[1].add(page)
        for vid in re.findall(r"youtube\.com/embed/([A-Za-z0-9_-]+)", source):
            videos.setdefault(vid, ("", set()))[1].add(page)

    for name in sorted(os.listdir(RAW_CMU)):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(RAW_CMU, name), encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        page = dict(CMU_NAV).get(name, name) + " (2010)"
        for vid in re.findall(r"youtube\.com/v/([A-Za-z0-9_-]+)", source):
            videos.setdefault(vid, ("", set()))[1].add(page)

    # Real titles and uploader channels, captured from YouTube's oEmbed endpoint so the
    # metadata survives here even if the videos themselves ever disappear.
    meta = {}
    meta_path = os.path.join(ROOT, "archive", "videos.json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)

    rows = []
    def sort_key(vid):
        info = meta.get(vid, {})
        return ((info.get("title") or videos[vid][0] or "￿").lower(), vid)

    for vid in sorted(videos, key=sort_key):
        caption, pages = videos[vid]
        info = meta.get(vid, {})
        label = info.get("title") or caption or vid
        author = info.get("author", "")
        author_cell = html.escape(author)
        if author and info.get("author_url"):
            author_cell = '<a href="%s">%s</a>' % (html.escape(info["author_url"]), html.escape(author))
        rows.append(
            '<tr><td><a href="https://www.youtube.com/watch?v=%s">%s</a>'
            '<br><span class="size">%s</span></td><td>%s</td><td>%s</td></tr>'
            % (vid, html.escape(label), vid, author_cell,
               html.escape(", ".join(sorted(pages))))
        )

    with open(os.path.join(ROOT, "videos.html"), "w", encoding="utf-8") as fh:
        fh.write(VIDEO_PAGE.format(rows="\n".join(rows), count=len(videos)))
    print("indexed %d videos" % len(videos))


def build():
    for directory in (OUT_CMU, OUT_WIKI):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

    count = 0
    for name in sorted(os.listdir(RAW_SITES)):
        if not name.endswith(".html"):
            continue
        title, body = extract(os.path.join(RAW_SITES, name), "sites-canvas-main-content")
        if not body.strip():
            print("  skip (no content): %s" % name)
            continue
        out_name = "index.html" if name in ("index.html", "home.html") else name
        if name == "home.html" and os.path.exists(os.path.join(OUT_WIKI, "index.html")):
            continue
        body = rewrite_wiki(body)
        with open(os.path.join(OUT_WIKI, out_name), "w", encoding="utf-8") as fh:
            fh.write(render(title, body, WIKI_NAV, out_name, WAYBACK_SITES, "wiki"))
        count += 1

    for name in sorted(os.listdir(RAW_CMU)):
        if not name.endswith(".html"):
            continue
        # Team.html and Research.html use a two-column template whose photo column
        # (#sidebar1) lives outside #mainContent, so the whole #container is taken and
        # the page chrome stripped afterwards.
        title, body = extract(os.path.join(RAW_CMU, name), "container")
        if not body.strip():
            print("  skip (no content): %s" % name)
            continue
        # the hand-written logo, nav row and page heading are replaced by the shell's chrome
        body = re.sub(r'<p align="center"><img src="About/PANDAILogo_new\.png"[^>]*/?>\s*</p>', "", body)
        body = re.sub(r'<div align="center"><strong><a href="index\.html">Home</a>.*?</div>', "", body, flags=re.S)

        # every 2010 page carries <title>PandAI</title>, so the real page name has to
        # come from the heading being stripped; fall back to the nav label.
        heading = re.search(r"<h1 align=\"center\"><strong>(.*?)</strong>\s*</h1>", body, re.S)
        if heading:
            label = re.sub(r"<[^>]+>", "", heading.group(1))
            label = html.unescape(label).replace("\xa0", " ").strip()
            if label:
                title = label
        body = re.sub(r"<h1 align=\"center\"><strong>.*?</strong>\s*</h1>", "", body, count=1, flags=re.S)
        if title == "PandAI":
            title = dict(CMU_NAV).get(name, title)
        body = rewrite_cmu(body)
        extra = " twocol" if 'id="sidebar1"' in body else ""
        with open(os.path.join(OUT_CMU, name), "w", encoding="utf-8") as fh:
            fh.write(render(title, body, CMU_NAV, name, WAYBACK_CMU, "cmu", extra))
        count += 1

    print("built %d pages" % count)
    build_video_index()


if __name__ == "__main__":
    build()
