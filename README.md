# Voca project page

Anonymous project page for the ICLR submission *Voca: Are Large Audio Language
Models Ready for Voice Companionship?*

Everything the page needs is in this folder. It is plain static HTML: no build
step, no framework, and no third-party requests — system fonts, inline SVG icons,
local audio files, and small scripts for scroll-reveal, navigation, audio playback
and the example gallery. With JavaScript disabled, all dimensions remain visible
and the native expandable examples still work.

```
voca-page/
├── index.html
├── .nojekyll                 # tells GitHub Pages to serve files as-is
├── tools/                    # optional gallery regeneration and selection manifest
├── pages/                    # 44 benchmark and 57 VocaAgent case pages
└── static/
    ├── audio/                # selected original WAVs under examples/ and voca-agent/
    ├── css/style.css
    ├── js/examples.js
    └── images/overview.png
```

## Audio

`static/audio/` holds every clip the page plays. They are referenced straight
from `index.html` with relative paths and play on click:

```html
<audio controls preload="none" src="static/audio/pc_para_hit_model.m4a"></audio>
```

The page links the original example audio plus 337 copied WAV files for the
VocaAgent gallery. The VocaAgent files preserve every selected input turn and
the recorded Default, Care, Agent 3 and final VocaAgent response audio without
re-encoding. The new audio manifest is `tools/voca-agent-media.json`.
The WAV files in `static/audio/examples/` are copied without re-encoding and
checked against source hashes recorded in `tools/example-media.json`.
`preload="none"` defers loading until playback is requested.

## Example gallery

The gallery contains 44 selected examples: ten user-state understanding cases,
eight emotional interaction cases, 21 proactive care comparisons and five
safety cases. Select a dimension, select a capability, then expand a case.
Opening another case in that capability closes the previous one; closing or
switching pauses its audio. Both tab levels support arrow keys, Home and End.
Dimension, capability and case IDs support direct URL fragments and history.

Each dimension has a second row of capability tabs. With JavaScript enabled,
only the selected dimension and capability are shown; returning to a dimension
remembers its last selected capability. A three-step guide and dimension-specific
reading tips explain the input, response and evaluation. Search is unnecessary:
controls expand or collapse cases only in the current capability and copy a
capability or example link. Without JavaScript, the links and all native
expandable cases remain available.

Examples include successes, partial scores and failures. Understanding uses
reference-answer matching; emotional interaction and proactive care use saved
audio-judge criteria; safety uses refusal labels from a text judge. Scores and
reasons are reproduced from the supplied records. Missing analyses, transcripts
or response audio are identified rather than invented. The driving example now
has its saved evaluations (Default 4/5, Care 5/5) and all six user recordings.

All selected conversations retain the available original user audio, assistant
history text, and relevant background constraints. Prompts and judge details can
be expanded. Raw records containing local source paths are not copied into the
public gallery.

The VocaAgent gallery contains 57 cases: the twelve explicitly selected
paralinguistic cases from the original package, its thirteen semantic and twelve
contextual cases, and all twenty environmental/emotional cases from the new
package. The paralinguistic total is 32. Outcome tabs distinguish higher recorded
scores from no gain/regressions; unavailable Default scores are labeled. Cases
that reuse Default are not labeled as improvements over Default.

The main page retains category tabs and case summaries. Each full example lives
in its own HTML file under `pages/examples/` or `pages/voca-agent/` and loads in
place when opened. This preserves the same browsing interface while keeping
`index.html` small. Each child page can also be opened independently; this is
the fallback when JavaScript is disabled or a fragment fails to load. No public
JSON files are loaded or displayed. Original source packages are not modified.

VocaAgent cards preserve all user audio turns, historical assistant text,
background constraints, Default/Care/final outputs, Agent 2 observations,
Agent 3 outputs where invoked, actual system prompts, and recorded audio-judge
criteria and reasons. Audio loaded after expansion also obeys single-player
playback and pauses when the case or its category is closed.

Proactive care includes 14 voice or background-cue cases, three semantic cases
and four contextual cases. The expanded selection covers nonverbal-only sniffing
and coughing, sneezing, barking, sadness, fear, anger and sobbing alongside the
existing cases. Equal scores retain their different failed criteria; the
aftercare activity example distinguishes a vocal-emphasis deduction from a
failure to remember the restriction. Nonverbal-only inputs are identified as
such instead of displaying a missing-transcript notice.

Every example displays its recorded `source-dataset` and, where available, its
type. For constructed examples, this field can identify the source text or task
rather than the entire recording. Emotion examples include sadness mistaken for
calm and both correct and incorrect recognition of a happy-to-sad transition.

To change the curated selection, edit `tools/example-selection.json`, then run:

```bash
python3 tools/build_examples.py
python3 tools/build_voca_agent_cases.py
```

Regeneration reads `../candidate_samples/` and selected folders under
`../用户理解/`, `../主动关怀_多样对比/` and `../副语言触发_不提升与下降/`,
which are only needed for this optional authoring step.
VocaAgent regeneration additionally reads `../VocaAgent_Fun_Qwen_50例试听/` and
`../VocaAgent_环境音与情感_20例试听/`. The published HTML, scripts and audio are self-contained.

## Preview locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Use the HTTP preview server for loading cases in place. When opening files directly, follow the standalone case links.

## Deploy on GitHub Pages

Host under a **freshly created throwaway account** — a personal account leaks
identity through the username, profile, followers and starred repos. Commit
author name and email are recorded in every commit, so set them locally:

```bash
git init
git config user.name "Anonymous"
git config user.email "anonymous@example.com"
git add .
git commit -m "Voca project page"
git remote add origin https://github.com/<anon-account>/<repo>.git
git branch -M main
git push -u origin main
```

Those `git config` calls are repository-local and do not touch your global git
identity. Then in the repo: **Settings → Pages → Source: Deploy from a branch →
`main` / `/ (root)`**. The page appears at
`https://<anon-account>.github.io/<repo>/` within a couple of minutes.

## Anonymity

The page contains no author names, affiliations, acknowledgements or funding
statements, loads no external fonts, analytics or CDN assets, and links to no
repository. It states that all data and evaluation code will be released upon
acceptance. Keep it that way while the paper is under review.

## Content still to fill in

Three evaluation runs are incomplete and show `–` on the page: Qwen3-Omni and
Step-Audio-R1.5 on safe companion behavior, and role-and-permission safety for
every system. The role-and-permission example still shows the benchmark input
without a model response or evaluation. Speaker-identity examples include their
original text-only responses and refusal classifications. On acceptance, add the code and data links, then the
author names and affiliations for the camera-ready version.
