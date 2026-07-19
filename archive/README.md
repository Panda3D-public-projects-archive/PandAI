# How this archive was rebuilt

`archive/raw/` holds the two source sites exactly as the Wayback Machine returned
them, unmodified. The pages under `site/` are that same content re-wrapped for the
web, with the deliberate deviations recorded below.

`tools/fetch_archive.sh` re-runs the retrieval; `tools/build_site.py` rebuilds `site/`
from `archive/raw/`. The generated pages are overwritten on every build — change the
build script, not the output.

## Deliberate deviations from the originals

- **Navigation and page chrome** are replaced by a shared shell; the original logo, nav
  row and page heading are stripped so they are not duplicated.
- **Flash video embeds** on the 2010 site — 20 `<object>`/`<embed>` blocks — are
  rewritten as YouTube iframes carrying the same video ID. No current browser can play
  the originals, so those pages would otherwise be blank.
- **Attachment links** point at the copies under `HistoricalVersions/` rather than the
  dead hosts.
- **Six team e-mail links on the 2010 site were broken in the original.** They were
  written as `../Templates/name@andrew.cmu.edu`, missing the `mailto:` scheme, so they
  resolved to paths that never existed. They are restored as real `mailto:` links; the
  addresses were always visible as page text either way.
- **The dark colour scheme is a fidelity requirement, not a style choice.** Both sites
  were light-on-dark and the recovered markup is full of inline `<font color="#FFFFFF">`;
  on a light background much of the text would be invisible.

## Videos

The demo videos are **not** mirrored here — they remain on YouTube, linked and embedded.
All 25 were confirmed actually playing, rendered in a browser rather than merely probed,
when this archive was assembled. They live on three channels: `SuperPandai`, `johnkol83`
and `AegisGrim`. Their IDs, titles and uploaders are stored in `archive/videos.json` so
that metadata survives even if the videos do not.

YouTube embeds do **not** work when the pages are opened straight off disk over `file://`
— the player rejects the null origin with "Error 153". Serve the directory over HTTP to
preview locally:

```
python3 -m http.server 8000    # then open http://127.0.0.1:8000/
```

## Provenance of the recovered files

The 2010–2012 archives under `HistoricalVersions/etc-cmu-2010-2012/` are kept separate
because they are different builds, not duplicates, even where a filename repeats — the
2012 `StaticObstacleDemo.zip` and the wiki's copy differ, for instance. Four files were
byte-identical across both sites and are stored once.

One caveat worth knowing before you use the mesh generator: the surviving
`BlenderMeshGen` expects your mesh on the **X-Z plane**, not the X-Y plane the Panda3D
manual documents. The manual describes an August 2010 rebuild that was only ever hosted
on the author's personal site and was never crawled — it is lost. See
`COMMUNITY-NOTES.md` for the full account.
