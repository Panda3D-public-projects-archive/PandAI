# PandAI — archive

PandAI is a game artificial-intelligence library for [Panda3D](https://www.panda3d.org/),
built by a student team at the Carnegie Mellon
[Entertainment Technology Center](https://www.etc.cmu.edu/) around 2010 and documented
through 2020. It provides steering behaviours (seek, flee, pursue, evade, wander,
arrival, flocking, path following, obstacle avoidance) and navigation-mesh pathfinding,
and shipped as part of Panda3D from version 1.7.0.

Both of the project's websites are gone. This repository preserves what was left: the
source and samples that had already been saved here, plus everything recoverable from
the Wayback Machine — 30 pages, 28 release/demo archives, 14 images and an index of the
25 demo videos.

**The rebuilt site is published from this repository via GitHub Pages** (`index.html`
at the repo root).

## What is here

| Path | Contents |
| --- | --- |
| `COMMUNITY-NOTES.md` | Bugs, workarounds and design notes gathered from the forum and Discord |
| `index.html`, `videos.html`, `notes.html` | Landing page, demo-video index and rendered notes |
| `site/wiki/` | The 2016–2020 Google Sites documentation, 22 pages |
| `site/etc2010/` | The original 2010 ETC project site, 8 pages |
| `archive/raw/` | The verbatim archived HTML both mirrors were built from, unmodified |
| `HistoricalVersions/` | Library releases, source drops and mesh-generator builds |
| `HistoricalVersions/samples/` | The 13 sample projects attached to the wiki |
| `HistoricalVersions/etc-cmu-2010-2012/` | The earlier, separately-packaged 2010–2012 releases and demos |
| `examples/` | 12 runnable Python samples with their models and textures |
| `meshgen_v1.0_src/` | C++ source of the standalone navigation-mesh generator |
| `BlenderMeshGen/` | Python navmesh exporter driven from Blender geometry |
| `assets/` | Stylesheet and recovered images for the site |
| `tools/` | The scripts that fetched the archive and rebuild the site |

### Examples

`examples/` holds twelve samples — `seek`, `flee`, `pursue`, `evade`, `wander`, `flock`,
`pathFollow`, `obstacleAvoidance`, `staticObstacles`, `dynamicObstacles`,
`unevenTerrainPathFinding` and a simplified variant. Unlike the code inside the archived
ZIPs these are Python 3. They are stylistically mixed: four subclass `ShowBase` directly,
the other eight use the older `DirectObject` pattern with a module-level `ShowBase()` and
a bare `run()`. All twelve byte-compile under Python 3; they have not been re-verified
against a current Panda3D. They need Panda3D with the `ai` module:

```
pip install panda3d
cd examples && python seek.py
```

### Downloads

Every archive under `HistoricalVersions/` is preserved exactly as it was distributed.
These are Panda3D 1.6/1.7-era builds and are **not** expected to run unmodified against a
current Panda3D — they are kept as historical artifacts. Highlights:

- `etc-cmu-2010-2012/PandaiV0.2.zip` — the earliest surviving release
- `etc-cmu-2010-2012/PandAI_v0.5_source.zip`, `PandaAIV0.5.zip` — the v0.5 pair
- `etc-cmu-2010-2012/PandaAI_1.0.zip`, `Pandai_v1.0.zip` — two v1.0 packagings
- `Pandai_v1.0_src.zip` — full v1.0 source with Doxygen documentation
- `BlenderMeshGen.zip`, `meshgen_v1.0_src.zip`, `meshgen_v1.0_exec.zip` — mesh tooling
- `etc-cmu-2010-2012/0.2 Documentation.docx` — the original v0.2 manual

The 2010–2012 archives are kept separate because they are **different builds**, not
duplicates, even where a filename repeats: for example the 2012 `StaticObstacleDemo.zip`
and the wiki's copy differ. Four files were byte-identical across both sites and are
stored once.

## Community knowledge

[`COMMUNITY-NOTES.md`](COMMUNITY-NOTES.md) collects what the archived documentation
does not tell you, gathered from the Panda3D forum (2009–2025) and Discord: the known
bugs and their workarounds, what the navmesh pipeline actually requires, the
`navmesh.csv` format, design explanations from the authors, and the project's timeline.
Everything there is attributed and linked, and claims that were never confirmed are
marked as such.

Two findings worth pulling out here:

- **The surviving Blender exporter expects your mesh on the X-Z plane**, not the X-Y
  plane the Panda3D manual documents. The manual describes an August 2010 rebuild that
  was only ever hosted on the author's personal site and was never archived — it is
  lost. Both surviving copies are byte-identical and are the earlier X-Z build, which
  is verifiable in `BlenderMeshGen/pythonMeshGen/BlenderMeshGen.py`. This resolves a
  contradiction that confused people on the forum for years.
- **AnimateDream's 2011 overhaul fork is not lost.** The link given on the forum,
  `github.com/AnimateDream/PandAI`, 404s because the account was renamed; the work
  survives at [StephenLujan/PandAI](https://github.com/StephenLujan/PandAI), and
  includes a copy of the pre-integration CVS source.

If you want to *use* PandAI today rather than study it, start from
[rayanalysis/pandai-samples](https://github.com/rayanalysis/pandai-samples) — an active
rewrite of the sample programs with modern navmesh generation.

This archive also supplies the files requested in
[panda3d/panda3d#1649](https://github.com/panda3d/panda3d/issues/1649), an open issue
reporting that the PandAI links in the Panda3D manual are dead and that the navmesh
converter source is lost.

## Sources

Recovered from these two captures:

- <https://web.archive.org/web/20201022234250/https://sites.google.com/site/etcpandai/>
- <https://web.archive.org/web/20170123102252/https://etc.cmu.edu/projects/pandai/index.html>

`tools/fetch_archive.sh` re-runs the retrieval; `tools/build_site.py` rebuilds `site/`
from `archive/raw/`. Editing the generated pages directly will be overwritten — change
the build script instead.

## What was changed in rebuilding

`archive/raw/` is untouched. The pages under `site/` are the same content re-wrapped, with
these deliberate deviations:

- **Navigation and page chrome** are replaced by a shared shell; the original logo, nav
  row and page heading are stripped to avoid duplicating it.
- **Flash video embeds** on the 2010 site (20 `<object>`/`<embed>` blocks) are rewritten
  as YouTube iframes carrying the same video ID. No current browser can play the originals.
- **Attachment links** now point at the copies in `HistoricalVersions/` instead of the
  dead hosts.
- **Six team e-mail links on the 2010 site were broken in the original** — they were
  written as `../Templates/name@andrew.cmu.edu`, missing the `mailto:` scheme, so they
  resolved to nonexistent paths. They are restored as real `mailto:` links; the addresses
  were always visible as page text.
- **The dark colour scheme is required, not decorative.** Both sites were light-on-dark
  and the recovered markup is full of inline `<font color="#FFFFFF">`; on a light
  background much of the text would be invisible.

The videos are **not** mirrored here — they remain on YouTube and are linked and embedded.
All 25 were confirmed actually playing (rendered in a browser, not just probed) when this
archive was assembled. They live on three channels: `SuperPandai`, `johnkol83` and
`AegisGrim`. `videos.html` lists every one, and their IDs, titles and uploaders are stored
in `archive/videos.json` so that metadata survives even if the videos do not.

Note that YouTube embeds do **not** work when the pages are opened straight off disk over
`file://` — the player rejects the null origin with "Error 153". Serve the directory over
HTTP to preview it locally:

```
python3 -m http.server 8000    # then open http://127.0.0.1:8000/
```

## Credit

PandAI was created at the Carnegie Mellon Entertainment Technology Center by Kyle Dolan
(producer), Deepak Murali Chandrasekaran, John Kolencheryl and Srinavin Nair
(programmers), Jy-Huey (Grace) Lin (artist) and Ruth Comley, advised by Mike Christel.

This is an unofficial preservation mirror. All content belongs to its original authors and
is reproduced here only so that a piece of Panda3D history stays reachable. If you are one
of the authors and want something removed, please open an issue.
