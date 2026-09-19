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
└── static/
    ├── audio/                # selected original WAVs under examples/
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

The page links 78 audio clips: 75 original WAV files from the candidate sample
selection and three existing M4A recordings for the role-and-permission item.
The WAV files in `static/audio/examples/` are copied without re-encoding and
checked against source hashes recorded in `tools/example-media.json`.
`preload="none"` defers loading until playback is requested.

## Example gallery

The gallery contains 30 selected examples: eight user-state understanding cases,
eight emotional interaction cases, nine proactive care comparisons and five
safety cases. Select a dimension, then expand a case. Opening another case in
that dimension closes the previous one; closing or switching pauses its audio.
Arrow keys switch dimension tabs. Case IDs support direct URL fragments.

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

To change the curated selection, edit `tools/example-selection.json`, then run:

```bash
python3 tools/build_examples.py
```

Regeneration reads `../candidate_samples/`, which is only needed for this optional
authoring step. The published HTML, scripts and audio are self-contained.

## Preview locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Opening `index.html` directly as a `file://` URL also works.

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
