# PandAI community field notes

The archived documentation tells you what PandAI was *supposed* to do. This file
records what people actually ran into, gathered from the Panda3D forum
(2009–2025), the Panda3D Discord, and the panda3d GitHub tracker.

**Contents:** [Status](#status--should-you-use-this) ·
[Bugs and workarounds](#known-bugs-and-workarounds) ·
[The navmesh pipeline](#the-navmesh-pipeline) ·
[navmesh.csv format](#navmeshcsv-format) ·
[How it works inside](#how-it-works-inside) ·
[Timeline](#timeline) ·
[Lost and recovered](#lost-and-recovered-resources) ·
[Alternatives](#alternatives)

---

## Status — should you use this?

PandAI still ships with Panda3D as `panda3d.ai`. It is unmaintained, and the
Panda3D core developers say so plainly:

> "PandAI was a student project, but it didn't receive proper mentoring, so it is
> not well-designed."
> — rdb, Panda3D Discord `#engine-dev`, 2019-03-04

> "In general, you are better off avoiding PandAI. It is an old student project
> that has not been maintained in quite some time."
> — Moguri, Panda3D Discord `#chat`, 2019-04-27

There was never an announcement that the project ended. The closest thing is the
lead developer winding down:

> "I don't see any future changes taking place to PandAI unless I get more free
> time out to do it."
> — NNair (Srinavin Nair), forum [#204](https://discourse.panda3d.org/t/6746/204), 2011-06-06

He also framed what it was for, which is the fairest way to judge it:

> "our vision was to make it as a learning tool or a starting AI tool."
> — NNair, forum [#187](https://discourse.panda3d.org/t/6746/187)

**If you want to actually use PandAI today**, start from
[rayanalysis/pandai-samples](https://github.com/rayanalysis/pandai-samples) — an
active (2024–2025) rewrite of the sample programs that replaces the old Blender
exporter with navmesh generation done on the fly, and works with modern Blender
and glTF. See [Alternatives](#alternatives) for non-PandAI options.

---

## Known bugs and workarounds

### Keep a Python reference to your AICharacter, or you get a hard crash

`AIWorld.addAiChar()` does not hold a Python-side reference. A local variable
goes out of scope, the object is destroyed, and Panda3D segfaults.

```python
aiChar = AICharacter(...)        # crashes later
self.aiChar = AICharacter(...)   # correct
```

Diagnosed by Bradamante, confirmed by NNair, forum
[#162–163](https://discourse.panda3d.org/t/6746/162): *"variables being local and
so when the scope goes out, the object is destroyed."* This is the most likely
cause of unexplained crashes.

A related assertion, `_world == nullptr at line 36 of contrib/src/ai/aiCharacter.cxx`,
appears when an `AICharacter` is constructed or added twice
(redeyedman4, Discord, 2020-03-25).

### `pathFollow` leaks a node every path — framerate collapses

Every call creates a NodePath named `dummy` and never removes it. Reported with a
minimal reproduction by jeroendenhaan
([forum 26203](https://discourse.panda3d.org/t/26203), 2020-06-24): 300+ fps down
to 50 within minutes. His workaround, immediately after `startFollow()`:

```python
render.find('dummy').removeNode()
```

### Motion is framerate-dependent

`AIWorld.update()` takes no delta time. Characters move at half speed on a machine
running at half the framerate — reported by ognjenk
([#203](https://discourse.panda3d.org/t/6746/203)), confirmed by NNair
([#204](https://discourse.panda3d.org/t/6746/204)), who said he would fix it first
if he ever returned to the project. He did not.

Note NNair had earlier answered the same question incorrectly
([#91](https://discourse.panda3d.org/t/6746/91): *"It is a threaded process and
there isn't any control to do that for now"*). Hypnos
([#90](https://discourse.panda3d.org/t/6746/90)) was already patching a `timeDelta`
into the acceleration term in his own build.

AnimateDream, after reading the source
([#188](https://discourse.panda3d.org/t/6746/188)):

> "The line `acceleration = _velocity;` in AICharacter::update() is all kinds of
> wrong. Force should not be retained between frames, velocity should… the whole
> thing appears to be frame rate dependent and has no regard for time."

### Scale bugs — characters stop short or never arrive

Arrival is tested as `int(target_distance) == 0`, i.e. "closer than one world
unit", with no regard for model scale. Found by Hypnos
([#96](https://discourse.panda3d.org/t/6746/96)) and independently by crolli
reading the source ([forum 9887 #55](https://discourse.panda3d.org/t/9887/55)).
NNair confirmed ([9887 #52](https://discourse.panda3d.org/t/9887/52)):

> "Yes PandAI has problems with scale. This is a bug which we did not get time to
> fix… our distance check from AI to target doesn't get adjusted based on scale."

**The sanctioned workaround, which NNair gave at least five times**, is the general
escape hatch for most of PandAI's limitations: make an *empty NodePath* the
AICharacter, let PandAI drive that, and copy its position and orientation onto your
real model each frame after `aiWorld.update()`. He recommends this for scale
problems, ODE/physics integration, turn-rate limiting, and pursue standoff distance.

### Constructor parameters are misleadingly named

`AICharacter(name, nodepath, mass, movt_force, max_force)` — the last one is a
**speed cap**, not a force. NNair
([#163](https://discourse.panda3d.org/t/6746/163)): *"Increasing the mass slows it
down / Increasing the movement force, increases the acceleration / This is the cap
on the maximum speed."* The model is `v = u + at`, `a = F/m`.

Changing the Python variable you passed in does nothing — values are copied. Use
`setMaxForce()` and friends ([9887 #27/#31](https://discourse.panda3d.org/t/9887/27)).

### `removeAi()` takes a behaviour name, not a character name

Valid: `"seek"`, `"pursue"`, `"pathfollow"`, `"all"`. Pathfinding counts as
`"pathfollow"`. To remove a character use `removeAiChar()`. The original docs said
`removeAi(string "AIName")`, which actively misled users; passing an instance name
just prints `invalid option!`
([#165–167](https://discourse.panda3d.org/t/6746/165)).

### The documented `priority` parameter does not exist

The docs describe an `int priority`; the real keyword arguments are `flock_wt`,
`wander_weight`, `evade_wt` and so on, and `.flock(priority=0.9)` raises. NNair
conceded the terms had been used interchangeably
([#175–176](https://discourse.panda3d.org/t/6746/175)). Flocking weights are also
poorly behaved: docs suggest 1–5, but Hodge1620 found anything above 1.0 "haywire"
and below 1.0 ineffective, and this was never resolved.

### Obstacle avoidance

- Obstacles must be **one-sided**: `obstacle.setTwoSided(False)` fixed characters
  passing straight through, per driver
  ([9887 #54](https://discourse.panda3d.org/t/9887/54)).
- High velocity defeats it — NNair: *"if the velocity is too high it cannot steer
  away effectively."*
- `addObstacle()` belongs to **pathfinding**, not steering behaviours; mixing the
  two is a common error ([9887 #39](https://discourse.panda3d.org/t/9887/39)).
- A long-standing `AssertionError: !is_empty()` from `AIworld.update()` was hit by
  several people ([forum 11057](https://discourse.panda3d.org/t/11057), 2011–2012)
  and never properly diagnosed. Mallku observed it appears once enough obstacles are
  added, regardless of distance between them. KnolanCross's workaround was to wrap
  the first `update()` in `try/except` — it then works from the second frame on,
  which nobody explained.

### Other confirmed quirks

- **Forward axis is hardcoded to -Y**, against Panda3D's own convention. drwr
  corrected the developers on this: *"the Panda convention is that +Y is the forward
  direction"* ([#74](https://discourse.panda3d.org/t/6746/74)). Added to the fix
  list; **no post confirms it was ever fixed.**
- **Wander is not seeded**, so it produces the identical trajectory every run, and
  the seed is not exposed to Python (sorcus,
  [#193](https://discourse.panda3d.org/t/6746/193)). Its "area of effect" is in
  absolute world coordinates and is only a soft constraint — *"a sort of tacked on
  feature… less than perfect."*
- **Only wander can be constrained to a plane.** Pursuing a target above or below
  sends characters flying or underground; the only offered fix is resetting Z and
  pitch yourself every frame ([#175](https://discourse.panda3d.org/t/6746/175)).
- **Pursue and evade do not lead their target** — they steer at its current
  position. `Pursue::get_target_velocity()` returns a hardcoded zero vector, because
  NodePath exposes no velocity (AnimateDream,
  [#184](https://discourse.panda3d.org/t/6746/184)).
- **Don't call `pursue()` after `pathFindTo()`** — *"Internally, it already does
  pursue to the chosen points in the pathfinder"* (NNair,
  [#147](https://discourse.panda3d.org/t/6746/147)).
- **`pathFindTo()` reports failure only by printing to the console** — no return
  value, so a failed path cannot be detected in code (wezu,
  [#216](https://discourse.panda3d.org/t/6746/216)).
- **`Pursue::Pursue()` never initialises `_pursue_direction`** (Hypnos,
  [#95](https://discourse.panda3d.org/t/6746/95)). Added to the bug list; fix status
  unknown.
- **`navmesh.csv` is read with plain C++ file I/O**, not through Panda's virtual
  file system or model path. Demos only work if you `cd` into their directory, and
  after `packp3d` the file is invisible to the loader. ognjenk's workaround was to
  write the CSV out to `multifileRoot` at startup and pass an absolute path
  ([#203](https://discourse.panda3d.org/t/6746/203)).

---

## The navmesh pipeline

This is where most people got stuck, and where the surviving documentation is
actively wrong.

### It is a waypoint grid, not a navigation mesh

JohnKol said so directly and apologised for the naming
([#97](https://discourse.panda3d.org/t/6746/97)):

> "we use waypoint meshes in PandAI as compared to Navmesh. And we know the
> confusion is due to the naming convention we used."

### Pathfinding is 2D, and supplying a 3D mesh will not help

> "the A* that we have implemented does not check for neighbor nodes in 3D space…
> even if you were to create your own 3D mesh, the A* wouldn't handle it currently."
> — JohnKol, [#56](https://discourse.panda3d.org/t/6746/56)

The `Height` column is always overwritten with 0. For multiple floors or stairs the
only approach offered was one mesh per level, switched manually.

### The surviving Blender exporter expects the X-Z plane

This resolves a contradiction that ran for years in the forum, and it matters
because the manual documents a version you cannot get:

- The Blender exporter was released 2010-07-18 requiring the mesh on the
  **X-Z plane** ([#122](https://discourse.panda3d.org/t/6746/122)).
- On 2010-08-05 NNair announced an updated exporter that used the **X-Y plane**
  instead ([#151](https://discourse.panda3d.org/t/6746/151)). The Panda3D manual
  documents this newer behaviour.
- That updated version was only ever published as `pythonMeshGen.zip` on
  `srinavinnair.com/downloads/`, which the Wayback Machine never crawled. **It is
  lost.**
- Both copies that survive — from the CMU site and the Google Sites wiki — are
  byte-identical (`md5 cceae05b952cec2ef5e7de6c198671e7`) and are the **older
  X-Z build**. Confirmed by reading the source in this repo:
  `BlenderMeshGen/pythonMeshGen/BlenderMeshGen.py` compares `getX()` against
  `getZ()` throughout.

**So: with the tool that survives, build your mesh on the X-Z plane.** The manual is
correct only for a version nobody has. This also explains powerpup118's otherwise
baffling advice in [#201](https://discourse.panda3d.org/t/6746/201) — *"even though
the manual states that the blender mesh generation script assumes that your mesh is
built on the X-y axis, it's wrong"* — he was right about the tool people actually had.

### Quads or triangles, depending on which tool

- **Max/Maya** (`meshgen.exe`) **requires** triangulation — run `egg-trans -C`.
- **Blender** (`BlenderMeshGen.py`) works on **quads** and must **not** be
  triangulated. NNair, [#139](https://discourse.panda3d.org/t/6746/139): *"This new
  meshgen uses quads and so triangulation is not needed."*

Triangulating first produces the signature error, which recurs throughout the thread:

```
File "BlenderMeshGen.py", line 71, in iterateEggPoly
    egg.getVertex(2), egg.getVertex(3))
AssertionError: index >= 0 && index < (int)size() at line 467 of built/include/eggPrimitive.I
```

Blender eggs are also incompatible with the original Max/Maya `meshgen.exe`, because
Blender orders vertices and quads differently — the symptom is a CSV that looks fine
but whose indices don't match node positions, so characters move but ignore obstacles
([#68](https://discourse.panda3d.org/t/6746/68)).

### Other pipeline requirements

- **Equal row and column counts.** Rectangular grids give non-square cells
  ([#97](https://discourse.panda3d.org/t/6746/97)).
- **Maya must be Z-up.** A Y-up scene silently swaps Length with Height and PosY with
  PosZ (Shoog, [#107](https://discourse.panda3d.org/t/6746/107)).
- **Scale 50 or above.** *"Much smaller meshes bug out a bit"* (NNair,
  [#151](https://discourse.panda3d.org/t/6746/151)), and don't rescale the planes at
  runtime.
- **Both source and destination must sit on traversable faces**, else you get
  `couldnt find source` / `couldnt find destination` — the most common error string
  in the whole thread.
- **Don't hand-edit the CSV**, and particularly don't re-save it through Excel's
  column splitter, which reintroduces errors even with the data untouched
  ([#127–128](https://discourse.panda3d.org/t/6746/127)). It is plain text and is
  *not* subject to Excel's row limit.
- Deleting collision tags and materials in the Blender source stopped `meshgen.exe`
  crashing for GarrickW ([#127](https://discourse.panda3d.org/t/6746/127)); he could
  not narrow down which was responsible. Avoid Blender layers; build from
  `Mesh->Plane` plus `W->Subdivide` rather than `Mesh->Grid`.

The single most useful reframing, from NNair
([#128](https://discourse.panda3d.org/t/6746/128)):

> "Try to think of the navigation mesh as separate from the terrain. The navigation
> mesh should be thought of as the underlying logic for where a character can move.
> The terrain can be thought of as the graphics over it."

Your nav grid does not have to match your visible geometry.

### Unresolved: the all-positive-coordinates anomaly

GarrickW ([#127](https://discourse.panda3d.org/t/6746/127)) reported that with a mesh
centred on the origin and vertices in all four quadrants, *"in the CSV file, all
values, X and Y, are positive."* matkod ([#211](https://discourse.panda3d.org/t/6746/211))
independently found he had to edit negative values in the CSV to make it work. **No
developer ever explained this, and no rule about mesh centring was ever established.**
Treat claims that "the mesh must be centred" as unverified.

---

## navmesh.csv format

The authoritative description, from JohnKol
([#56](https://discourse.panda3d.org/t/6746/56)):

```
Grid Size  - size of the mesh
NULL       - 0 = node exists, 1 = does not exist
NodeType   - 0 = main node, 1 = neighbor node
GridX      - row index
GridY      - col index
Length     - length of each cell
Width      - width of each cell
Height     - currently overwritten as 0 since height info is not used
PosX/Y/Z   - position of the node in the cell (world space, centre of the grid cell)
```

Each main node row is followed by its eight neighbour rows — nine rows per cell, so a
grid of N×N cells yields `(N*N)*9` data rows. Neighbours that do not exist are written
as `1,1,0,0,0,0,0,0,0,0`.

Row order is significant: the rows are read sequentially into a vector. JohnKol
believed the grid starts at the bottom-left but said *"if I am not mistaken, I will
confirm this anyhow"* — **he never did.**

`examples/contrib/geomipterrain_navmesh.py` in this repo is a working reference
implementation of this layout, recovered from the forum.

---

## How it works inside

Explanations from the authors that never made it into the documentation.

**Dynamic obstacles.** JohnKol, [#56](https://discourse.panda3d.org/t/6746/56):

> "the way the pathfinding system understands obstacles that have been added
> dynamically during runtime is by first calculating the area of the obstacle and then
> setting a property of all the nodes which fall within the area to 'false' or
> non-traversable."

Removal is the inverse, but was never exposed to Python — *"With a little coding in
C++ this can be easily done."*

**How A\* rejects nodes.** A non-existent node is stored as null when the CSV is read
into the vector; the A\* does a null check for traversability
([#97](https://discourse.panda3d.org/t/6746/97)). The cost function is purely
distance-based.

**Why every character loads its own copy of the navmesh** — deliberate, not an
oversight ([#56](https://discourse.panda3d.org/t/6746/56)):

> "We needed an instance of the navmesh for each AI character since we wanted to
> dynamically avoid other AI characters during pathfinding."

Memory therefore scales linearly with agent count. peerpanda's team patched it to share
one mesh at the cost of allowing only one A\* at a time
([#86](https://discourse.panda3d.org/t/6746/86)); that patch was never published.

**Why not Recast & Detour** — NNair, [#40](https://discourse.panda3d.org/t/6746/40):

> "since this was a semester project where we had to implement both steering behaviors
> and path finding, we had to opt for the more simplistic solution of navigation mesh
> creation by the artist… in order to integrate Recast and Detour into Panda3D, we
> would have had to thoroughly understand the intricacies of his code and the challenge
> of wrapping his code base into python. This would have been time consuming."

**Relationship to the textbook steering literature.** NNair
([#187](https://discourse.panda3d.org/t/6746/187)): *"we did refer his [Craig Reynolds']
paper for some of our work but modified them a little bit to work differently in some
implementations."* Worth knowing if you are trying to reconcile PandAI's behaviour
against OpenSteer or the original boids paper.

---

## Timeline

| Date | Event |
| --- | --- |
| 2009-08-27 | sorcus opens [the development thread](https://discourse.panda3d.org/t/6746) asking the community what an AI library should do |
| 2009-11-04 | **v0.5** — seven steering behaviours: seek, flee, pursue, evade, arrival, wander, flock |
| 2009-11-04 | rdb posts a Makefile so non-Windows users can build it (only `BuildDLL.bat` shipped) |
| 2009-12-09 | **v1.0** — adds obstacle avoidance, path following, the navmesh tool and A\* pathfinding. Announced as going into the Panda3D CVS trunk for 1.7 |
| 2010-01-10 | Panda3D daily builds already include PandAI |
| 2010-01-13 | rdb changes the import from `libpandaai` to **`panda3d.ai`** — the core integration was done by rdb, not the CMU team |
| 2010-07-18 | Blender mesh generator released — **X-Z plane** |
| 2010-08-05 | Updated Blender mesh generator — **X-Y plane**. *This build is now lost* |
| 2010-10-19 | NNair: the CMU site can no longer be updated — *"being graduates we have lost access and freedom to edit it"* |
| 2010-12-26 | Documentation moves to the Google Sites wiki |
| 2011-01-10 | v1.0 ships with `EXPCL_PANDAAI` export macros applied in Panda3D 1.7.1, making C++ use practical |
| 2011-02-06 | PandAI documentation merged into the official Panda3D manual |
| 2011-03-07 | rdb: canonical source lives in `contrib/src/ai` |
| 2011-06-06 | NNair's effective end-of-maintenance statement |
| 2011-08-15 | AnimateDream publishes an overhaul fork |
| 2015-03-16 | Last post in the development thread — wezu asks if anyone will update it for 1.9. No reply |
| 2024-04-27 | rayanalysis files [panda3d#1649](https://github.com/panda3d/panda3d/issues/1649): the PandAI links in the manual are dead and `BlenderMeshGen.py` is lost |
| 2024-05-26 | Simulan announces [pandai-samples](https://github.com/rayanalysis/pandai-samples), reviving PandAI with modern navmesh generation |
| 2025-06-27 | A user reports the mesh generator download 404s ([forum 31181](https://discourse.panda3d.org/t/31181)) — still broken |

The developers answered nearly every user post, often within hours, for about
eighteen months, and repeatedly named their own project's limitations rather than
deflecting. Several features — Blender support, the Linux mesh generator, the plane
change — shipped directly in response to thread reports.

---

## Lost and recovered resources

**Recovered by this archive**, and enough to close
[panda3d#1649](https://github.com/panda3d/panda3d/issues/1649):

- Both project websites, 30 pages — see `site/`
- `BlenderMeshGen.zip`, including `pythonMeshGen/` — the exporter the issue calls lost
- 28 release and demo archives, v0.2 through v1.0
- Chia_Pet's heightmap navmesh generator, recovered intact from the live forum after
  the copy in the scraped corpus turned out to have its comparison operators mangled →
  `examples/contrib/geomipterrain_navmesh.py`

**Recovered elsewhere:**

- **AnimateDream's overhaul fork.** The link given in the forum,
  `github.com/AnimateDream/PandAI`, 404s — the account was renamed. It survives at
  [StephenLujan/PandAI](https://github.com/StephenLujan/PandAI): created 2011-08-15,
  the exact date of the forum post, first commit *"Original PandAI from cvs"*, with
  later commits authored as "AnimateDream". It replaces the physics, adds a steering
  base class and nestable weighted composite objectives. The author described it as
  unfinished and put it on hold in 2012 — but it also contains **a copy of the
  pre-integration CVS source**.

**Genuinely lost** — never crawled by the Wayback Machine:

- `srinavinnair.com/downloads/` and its four attachments: `ai.zip` (described as *"the
  latest source code"*), `pythonMeshGen.zip` (the corrected X-Y Blender exporter),
  `pythonPathfinding.zip` (a full test case with meshes and navmesh), and
  `PandaiPursueTest.zip`. Only the listing page survives, from 2019.
  The `ai.zip` content is likely equivalent to the CVS import in StephenLujan/PandAI;
  the corrected exporter is not.
- `sin3.de/pandai/` — peerpanda's reproduction files. No captures at all.
- peerpanda's shared-navmesh patch — described in the thread, never published.
- Test assets on `uploading.com` (host defunct) and several pastebins.

Possibly still worth checking: the Launchpad bug tracker, where NNair actually filed
PandAI bugs under a "PandAI" tag, and the pre-integration CVS history.

---

## Alternatives

Endorsed by PandAI's own authors and by the core developers:

- **[Recast & Detour](https://github.com/recastnavigation/recastnavigation)** — the
  most-recommended option, including by NNair himself. et1337 got Recast output into
  Panda3D via `.obj` → Blender → `.egg` and wrote his own A\* over it
  ([#108](https://discourse.panda3d.org/t/6746/108)).
- **[wezu/p3d_astar_nav](https://github.com/wezu/p3d_astar_nav)** — a small pathfinding
  and navmesh-graph script for Panda3D, usable in 2D and 3D, with obstacle detection,
  follow, aggro, avoid, flee and multi-level travel. This was the accepted answer when
  a user hit the dead PandAI downloads in 2025.
- **[OpenSteer](https://opensteer.sourceforge.net/)** / Craig Reynolds'
  [steering behaviours](https://www.red3d.com/cwr/steer/) — *"much more specific and
  mature"* (AnimateDream). The PandAI research pages cite Reynolds throughout.
- **PandaSteer** — the predecessor rdb pointed at in 2009; already unmaintained then.

---

## Sources

- Panda3D forum, primarily [t/6746](https://discourse.panda3d.org/t/6746) (216 posts,
  2009–2015) and [t/9887](https://discourse.panda3d.org/t/9887) (58 posts, 2010–2013),
  plus roughly a dozen smaller threads through 2025.
- The Panda3D Discord, `#chat`, `#help` and `#engine-dev`, 2019–2026.
- [panda3d/panda3d#1649](https://github.com/panda3d/panda3d/issues/1649).

Quotations belong to their authors and are reproduced here so that hard-won findings
scattered across fifteen years of threads stay findable. Where this file states
something as fact, it is because a developer confirmed it in-thread or it was verified
directly against the code in this repository; everything else is marked as unverified.
