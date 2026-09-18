# Voca project page

Static project page for the Voca benchmark. No build step and no third-party
requests: system fonts only, inline SVG icons, and a small inline script for
smooth scrolling, scroll-reveal, active-nav highlighting, and back-to-top. The
script is progressive enhancement, so all content is present and readable with
JavaScript disabled.

```
voca-page/
├── index.html
├── .nojekyll                     # tells GitHub Pages to serve files as-is
├── scripts/gen_audio.sh          # regenerates the placeholder demo clips
└── static/
    ├── css/style.css
    ├── audio/           # placeholder example clips (macOS `say` TTS)
    └── images/overview.png
```

## Preview locally

```bash
cd voca-page
python3 -m http.server 8000
# open http://localhost:8000
```

## Before publishing

This is a submission-stage, double-blind page: it shows no authors, no
affiliations, and no code/repository link, and it states plainly that
"All data and evaluation code will be released upon acceptance." Keep it that
way until the paper is accepted.

1. **Replace the overview image.** `static/images/overview.png` is currently a
   screenshot of the compiled figure and still has the `Figure 1: overall`
   caption strip at the bottom. Export the source figure to PNG at roughly
   2000 px wide and overwrite the file.
2. **Add safe companion behavior numbers** once finalized. The placeholder note
   sits directly below the main leaderboard table, and the SCB dimension can
   then get its own per-capability table alongside USU and EI.
3. **Fill the podium.** The three champion / runner-up / third-place slots in
   the leaderboard are keyed to the Overall column. When Overall is ready, edit
   the podium markup and add the `gold` / `silver` / `bronze` class to the
   matching `<tr>` in the main table to tint and badge that row.
4. **Replace the example audio.** The clips under `static/audio/` are macOS
   `say` TTS placeholders, not model inputs/outputs. Regenerate or overwrite
   them (see `scripts/gen_audio.sh`), keeping the same filenames. The visible
   "placeholders synthesized locally" disclaimer in the Examples section can then
   be removed.
5. **On acceptance**, add the real code/data link and, for the camera-ready
   version, the author names and affiliations.

## Anonymity checklist

Double-blind review means the page itself must not identify the authors, and
neither must the hosting account.

- The page contains no author names, affiliations, acknowledgements, or funding
  statements, and loads no external fonts, analytics, or CDN assets. Keep it
  that way when editing.
- Host under a **freshly created throwaway GitHub account**. A personal account
  leaks identity through the username, profile, followers, and starred repos.
- Strip git history before pushing, since commit author name and email are
  recorded in every commit:
  ```bash
  cd voca-page
  git init
  git config user.name "Anonymous"
  git config user.email "anonymous@example.com"
  git add .
  git commit -m "Voca project page"
  ```
  Note the `git config` calls are repository-local, so they do not touch your
  global git identity.
- Check the image for leaks before uploading. Screenshots can carry window
  titles, file paths, and user names, and PNG/PDF exports can carry author
  metadata.

## Deploy on GitHub Pages

```bash
# in the throwaway account, create an empty public repo, then:
git remote add origin https://github.com/<anon-account>/<repo>.git
git branch -M main
git push -u origin main
```

Then in the repo: **Settings -> Pages -> Source: Deploy from a branch ->
`main` / `/ (root)`**. The page appears at
`https://<anon-account>.github.io/<repo>/` within a couple of minutes.

## A note on anonymous.4open.science

`anonymous.4open.science` anonymizes a repository for review, but it serves
files through its own viewer rather than rendering HTML as a website, so it is
suitable for the code and data link and not for a live project page. Use
GitHub Pages under a throwaway account for the page, and 4open.science for the
artifact link if you prefer its anonymization guarantees.
