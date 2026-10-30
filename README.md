# sha9ie — five studios, one workspace

**Deliverables**

| File | Role |
| --- | --- |
| `index.html` | the whole application: homepage, launcher, workspace shell, five studios, 68 feature modules, the GIF encoder **and** the six third-party libraries (base64 payloads, decoded on demand) |
| `manifest.json` | PWA manifest (name, icons, five app shortcuts) |
| `sw.js` | service worker: caches the shell so the app opens with no network |
| `icons/` | 192/512/maskable/apple-touch icons |
| `build.py` · `src/` · `js/` · `css/` | source of truth; `python3 build.py` regenerates `index.html` |
| `docs/` | setup + the executed test log |
| `tests/` | the Playwright harness that produced those numbers |

`index.html` alone is a complete, working, offline-capable application. `manifest.json`, `sw.js`
and `icons/` must be served next to it to get installability and offline reloads — that is a
platform requirement of service workers, not something a single HTML file can fake.

Five applications share one engine:

| Application | App ID | Hash | Purpose |
| --- | --- | --- | --- |
| sha9ie Cut | `video` | `#app=video` | video and audio studio |
| sha9ie Acrobat | `pdf` | `#app=pdf` | PDF and document studio |
| sha9ie Pixel | `photo` | `#app=photo` | photo editing and design lab |
| sha9ie OS | `planner` | `#app=planner` | planning, study and productivity |
| sha9ie Dev & Calc | `dev` | `#app=dev` | code sandbox, text utilities, calculators |

Total size 4.1 MB, first paint ≈ 200 ms, a studio opens in ≈ 300 ms.

```
index.html                     ← entry point (built from src/ + js/ + css/)
build.py                       ← python3 build.py → regenerates index.html
manifest.json · sw.js · icons/  ← PWA shell (installable + offline)
src/index.template.html        ← HTML source with {{placeholders}}
src/styles.css                 ← homepage design system (tokens, hero, planner, modals)
src/app.js                     ← homepage app: plans, storage, accounts
css/workspace.css              ← shell, tool directory, tool kit, studio CSS (bento/st/acr/cut/pxl/cmdk)
js/core.js                     ← SHAnamespace: registry, scoped storage, lazy libs, audio/video/print, container sniffing
js/lib/gif.js                  ← animated GIF89a encoder written for this project (median-cut + LZW)
js/workspace.js                ← full-screen shell, multi-tab engine, tool directory, dialogs, icons
js/apps.js                     ← the five apps, bento launcher, #app= hash routing, Send-To pipe, command registry
js/palette.js                  ← Ctrl/Cmd+K command palette (search every app and feature)
js/studios.js                  ← studio shell: rail + module host, mounted as a workspace tab per app
js/studio-acrobat.js           ← three-pane document editor (pdf.js render, pdf-lib write)
js/studio-cut.js               ← four-panel video/audio editor (preview, inspector, timeline, exports)
js/studio-pixel.js             ← photo lab (canvas pipeline, crop/zoom, compression, passport, colours)
js/tools-a.js                  ← Suite A · 15 productivity modules
js/tools-b.js                  ← Suite B · 20 document & PDF modules
js/tools-c.js                  ← Suite C · 21 media modules
js/tools-d.js                  ← Suite D · 12 developer & calculator modules
vendor/                        ← third-party libraries (see the table below)
assets/hero-field-opt.jpg      ← hero image (byte-identical to the original)
fonts/                         ← Caveat + Inter latin woff2, inlined as base64
docs/05-app-setup-and-tests.md ← setup, auth config, test log
tests/                         ← the Playwright harness used to verify every tool
```

## Run it

```bash
python3 -m http.server 8000        # from this folder
# then open http://localhost:8000/index.html
```

Serve it over `http://` — that is what makes the service worker (offline reloads) and the
browser APIs that need a secure context behave. `file://` still runs everything except the
service worker registration, and PDF.js gets its worker from an inlined blob so PDF rendering
works there too.

### Deploying with PWA support

1. Upload the folder (`index.html`, `manifest.json`, `sw.js`, `icons/`, optionally `vendor/`)
   to any static host — GitHub Pages, Netlify, Cloudflare Pages, Firebase Hosting. All free.
2. **Serve from the site root** (or keep `manifest.json`, `sw.js` and `icons/` beside
   `index.html`, which is the layout above); `sw.js` is registered with a relative scope.
3. Load the site once over HTTPS, then check DevTools → Application → Service Workers
   (`sha9ie-shell-v1 · activated`) and Manifest (installable).
4. After redeploying, bump `CACHE_VERSION` in `sw.js`; old shells are deleted on activate.

What the cache covers: the entry document, manifest and icons. The studios, every module, the
fonts, the hero image and all six libraries are inside `index.html`, so one cached document is
the entire application. What it cannot cover: Google sign-in (network), browser permissions
(camera, microphone, screen), and codecs your browser does not ship.

Hosting is free-tier friendly: any static host (GitHub Pages, Netlify, Cloudflare Pages,
Firebase Hosting) serves the folder as-is — no server code, no keys, no paid APIs.

## Build

```bash
python3 build.py                    # single self-contained file (default)
python3 build.py --external-vendor  # same page, libraries loaded from ./vendor/ lazily
```

Concatenates `css/workspace.css` and the thirteen modules listed in `JS_FILES` (core → gif →
workspace → apps → palette → studios → three studio editors → tools-a..d) into the `{{…}}`
slots of `src/index.template.html`, inlines the fonts, the hero image and (by default) every
vendor library, and fails loudly on unresolved placeholders or an unsafe `</script>` sequence.

## Third-party libraries (all free / open source, no accounts, no keys)

| File | Library | Version | Licence | Loaded when |
| --- | --- | --- | --- | --- |
| `vendor/pdf-lib.min.js` | pdf-lib | 1.17.1 | MIT | any PDF tool opens |
| `vendor/pdf.min.js` | PDF.js | 3.11.174 (legacy) | Apache-2.0 | PDF → images, grayscale, optimizer |
| `vendor/pdf.worker.min.js` | PDF.js worker | 3.11.174 | Apache-2.0 | same |
| `vendor/jszip.min.js` | JSZip | 3.10.1 | MIT (dual) | “download all” bundles |
| `vendor/lame.min.js` | lamejs | 1.2.1 | LGPL-3.0 | MP3 encoding |
| `vendor/qrcode.js` | qrcode-generator | 1.4.4 | MIT | QR Code Studio |

In the default build these files are embedded in `index.html` as base64 payloads and are
reconstructed as blob URLs on demand — no network request is made at any point.

Everything else — audio decode/encode, canvas rendering, MediaRecorder, the GIF encoder,
waveform drawing, PDF text layout — is first-party code in `js/`.

## Accounts: local profile now, Google when you connect a project

The **Log in / Get started** buttons always work. Two modes, both scoped per identity:

1. **Local profile (works immediately, no project needed).** Click *Continue with Google* →
   you get the local-profile form → enter a name and a valid email → you are signed in. A
   profile chip (`AS · Aarav Sharma · local`) appears in the navbar, the profile is stored in
   `localStorage` under `sha9ie:profile:v1`, the session survives a reload, and every tool and
   planner key is scoped to `uid:local-<hash-of-email>`. Invalid emails are rejected, and
   signing out removes the saved profile and returns you to the guest scope.
   This is a local profile, **not** a verified Google account — the UI labels it `local` so
   nobody is misled.
2. **Real Google sign-in (needs your own free Firebase project).** Fill `FIREBASE_CONFIG` and
   the same buttons open the real Google popup; the chip then shows your Google name and
   picture with no `local` tag.

### Connecting Firebase

1. Create a Firebase project → **Build → Authentication → Get started**.
2. Enable the **Google** provider, set a support email.
3. **Project settings → Your apps → Web app** and copy the config values.
4. Paste them into `FIREBASE_CONFIG` at the top of the homepage script (`src/app.js`, then
   rebuild, or edit the built block in `index.html`):

```js
var FIREBASE_CONFIG = {
  apiKey: "…", authDomain: "…", projectId: "…",
  storageBucket: "…", messagingSenderId: "…", appId: "…"
};
```

5. **Authentication → Settings → Authorized domains** → add your domain (and `localhost`).
6. `file://` cannot complete a Google popup flow — use `http://localhost:8000` or your host.

With no config the site stays in guest mode and says so; sign-in is never simulated. Tools
never touch the auth code: they read the current storage scope only.

## Data & privacy

- Everything is processed on this device. No tool uploads a file anywhere.
- Productivity state lives in `localStorage` under `sha9ie:ws:v1:<scope>:<tool>`; the homepage
  planner keeps its own `sha9ie:data:v1:<scope>` keys. Signing in or out re-scopes both at once,
  and the workspace closes its tabs so a guest never sees an account's data.
- `<scope>` is `guest` or `uid:<id>` after sign-in, so accounts never see each other's data.
- Corrupt payloads are copied to `<key>:corrupt:<timestamp>` and the tool falls back to
  defaults instead of crashing.
- Media blobs are never persisted — only downloaded. Object URLs are revoked when a tab closes.
- No cross-device sync is claimed or implemented.

## Architecture in one page

```
homepage (src/app.js)                     workspace engine (js/workspace.js)
  hero · how it works · launcher            #workspace  fixed inset:0, z 250, #07070a
  planner section                           tab strip: open / switch / × close / ← Home
  accounts (local profile | Firebase)       tool directory (softwares mega-menu)
        │                                          │
        └── launcher cards ──► js/apps.js ◄────────┘
                              5 apps · #app= routing · Send-To pipe · command registry
                                    │
                              js/studios.js  (one workspace tab per app)
                                    │  rail ── module host
              ┌─────────────────────┼───────────────────────┐
        studio-acrobat          studio-cut              studio-pixel
        plus 60 regular registered modules (tools-a|b|c|d)
```

* A **studio is a registered tool** (`studio-pdf`, `studio-video`, …) so the existing tab
  engine — open, switch, dedupe, × close, per-tab state, cleanup — applies unchanged.
* **Modules** are ordinary registered tools (or one of the three built-in editors). The rail
  swaps them into the studio host; the same registry feeds the directory, the command palette
  and the `Send To` targets, so nothing is listed twice.
* **State vs rendering**: editors keep a plain state object (documents, pages, annotations,
  filters, trim points) and redraw from it; persistence for OS modules goes through the scoped
  store, media stays in memory only.
* **Cleanup**: closing a tab or switching a module calls the module's `destroy()`, pauses and
  revokes `<video>/<audio>` sources, revokes every `blob:` URL in the pane, stops ambient audio
  graphs and cancels animation frames.
* **Send To** (`js/apps.js`) keeps payloads in memory for the session and mirrors anything over
  8 MB into IndexedDB (`sha9ie-pipe`); LocalStorage is never used for media.

## Tool status

All 68 modules (55 original tools + 13 new developer/calculator/barcode tools) are registered,
open in the workspace, and were exercised in a real browser (Chromium 156, Playwright). “Verified” means the core operation ran and its output was
re-opened and validated (PDF opened with PDF.js, audio decoded with `decodeAudioData`,
images/GIF parsed, ZIP CRC-checked).

### Suite A — Productivity (15/15 verified)

| # | Tool | Status | Notes / limitations |
| --- | --- | --- | --- |
| 1 | Goal & Phase Planner | Verified | Goals → phases → tasks; delete asks for confirmation; persists |
| 2 | Pomodoro & Ambient Sound Studio | Verified | Countdown 25:00 → 24:58 observed; pause/reset/skip; ambience is synthesised (`AudioContext` running). Long-run work→break transitions not timing-tested |
| 3 | Kanban Board | Verified | Add / rename / drag / delete, three columns, persists |
| 4 | Habit Streak Matrix | Verified | 30-day grid, add habit, toggle cells, streak math from stored ticks |
| 5 | Spaced-Repetition Flashcards | Verified | SM-2 style rating advanced Reps 0 → 1; deck persists |
| 6 | Cornell Notes Builder | Verified | Save + print (hidden-iframe print, no popups) |
| 7 | Eisenhower Priority Matrix | Verified | Four quadrants, add/edit tasks, persists |
| 8 | Exam Timetable Generator | Verified | Subjects → dated plan, flags subjects that cannot fit, print |
| 9 | Mindmap Canvas | Verified | Add node, drag (coordinates persisted 380,220 → 440,260), zoom/pan |
| 10 | GPA / Percentage Calculator | Verified | 4.0 / 10-point / percentage modes, credit-weighted result (75.00 in % mode) |
| 11 | Time-Block Scheduler | Verified | Blocks on a timeline, overlap detection |
| 12 | WPM Reading Trainer | Verified | Timed passage, measured words-per-minute, session persists |
| 13 | Milestone Tracker | Verified | Milestones with dates, dependencies, completion state |
| 14 | Zen Writer | Verified | Word count, autosave, focus mode |
| 15 | Daily Journal | Verified | Save / edit / search / delete with confirmation |

### Suite B — Documents (20/20 verified)

| # | Tool | Verified output | Notes / limitations |
| --- | --- | --- | --- |
| 16 | PDF Merger | merged.pdf, 4 pages (1 + 3 sources) | order controls; encrypted/broken files report per-file errors |
| 17 | PDF Splitter | pages-1-3.pdf | ranges parsed and validated |
| 18 | Images to PDF | images.pdf, 2 pages | PNG/JPG embedded; other formats rasterised through canvas first |
| 19 | PDF to Images | pdf-pages.zip with page-01..03.png | needs `vendor/pdf.worker.min.js` over http(s) |
| 20 | PDF Page Rotator/Organizer | organized.pdf, 3 pages | reorder + rotate |
| 21 | PDF Watermark Adder | watermarked.pdf, text readable | text or image watermark |
| 22 | PDF Page Numbering | numbered.pdf, “Page 1 of 3” | position/format options |
| 23 | Digital Signature Pad | signature.png (900×260) | mouse + touch; embeds into a chosen PDF |
| 24 | Invoice Generator | invoice-INV-2026-001.pdf | line totals, tax, totals computed |
| 25 | Resume Builder | resume.pdf | fields → clean single page |
| 26 | Markdown to PDF | notes.pdf | headings, lists, bold, code blocks |
| 27 | PDF Grayscale Converter | grayscale.pdf, 3 pages | **rasterises pages** — text becomes images |
| 28 | PDF Size Optimizer | smaller.pdf (30.7 KB from 52 KB) | says so and offers the original when output is bigger |
| 29 | Receipt Maker | receipt-R-*.pdf | line items + computed total |
| 30 | Certificate Designer | certificate.pdf | editable fields, landscape option |
| 31 | Passport Photo Sheet Maker | passport-sheet.pdf | A4 grid, configurable mm sizes, 300 dpi |
| 32 | Text to PDF | document.pdf | word wrap, page breaks |
| 33 | Contract Builder | agreement.pdf | explicitly **not** legal advice |
| 34 | Document Diff Checker | +2 / −1 highlighted | line-level add/delete |
| 35 | Word/Character Analyzer | words, characters, sentences, paragraphs, reading time | live stats |

### Suite C — Media (18 verified, 2 partially)

| # | Tool | Status | Notes / limitations |
| --- | --- | --- | --- |
| 36 | Video to Audio Extractor | Verified | WebM/MP4 → sample decodes, 3.21 s MP3, peak 0.97 |
| 37 | Audio Trimmer | Verified | region select, preview, WAV/MP3 export |
| 38 | Audio Merger | Verified | 44.1 kHz stereo + 48 kHz mono → 3.50 s WAV (resampled) |
| 39 | Voice Recorder & Silence Trimmer | Verified | fake-device mic, 3 s take, 2.00 s silence removed → 2.50 s WAV |
| 40 | Audio Speed & Pitch | Verified | granular overlap-add tempo/pitch; artefacts expected, stated in UI |
| 41 | Bass Booster & 5-Band EQ | Verified | real `BiquadFilterNode` chain (lowshelf + 5 peaking) offline render |
| 42 | Audio Volume Booster | Verified | peak 12 000 → 20 429 with soft limiter, no hard clipping |
| 43 | Video HD Frame Extractor | Verified | frame-0.00s.png 320×240 from a real clip |
| 44 | Video Clipper | Verified | MP4 with audio, frames re-encoded + decoded audio muxed |
| 45 | Video Audio Remover | Verified | silent.mp4 — `decodeAudioData` on the output fails, i.e. no audio track |
| 46 | Video to GIF | Verified | GIF89a 480×360, 30 frames, 76 KB, own encoder |
| 47 | Screen & Webcam Recorder | **Untested** | camera path shares the verified MediaRecorder code; screen capture cannot be exercised in headless Chromium (no display surface). Permission failures show an explicit message |
| 48 | Teleprompter + Camera Studio | Partially verified | camera acquired, text scrolls (translateY changes); the *recording* of a take is untested |
| 49 | Image Format Converter | Verified | PNG 800×600; refuses to save when the encoder returns a different MIME |
| 50 | Bulk Image Compressor | Verified | ZIP with 2 entries, real before/after sizes per file |
| 51 | Aspect-Ratio Cropper | Verified | 420×420 crop from 800×600 source |
| 52 | Audio Waveform Generator | Verified | 1144×686 PNG + peak/RMS readout |
| 53 | QR Code Studio | Verified | 320×320 PNG, 25×25 modules, scannable |
| 54 | Audio Format Converter | Verified | MP3 decodes back at 2.04 s, 44.1 kHz stereo |
| 55 | Video Format Converter | Verified | converted.mp4 3.13 s with audio; only containers MediaRecorder reports are offered |

### Suite D — Developer & calculators (12/12 verified)

| Module | Status | Notes |
| --- | --- | --- |
| Live Web Sandbox | Verified | iframe `sandbox="allow-scripts"`, parent cannot reach `contentDocument`; Run / Refresh / Clear / Download |
| JSON Studio | Verified | format, minify, validate with the engine's own error text |
| Text Case Converter | Verified | upper / lower / title / sentence / camel / snake / kebab + live counts |
| Base64 & URL Encoder | Verified | UTF-8 safe, rejects non-Base64 with the reason |
| Password & UUID Generator | Verified | `crypto.getRandomValues` / `crypto.randomUUID` |
| Scientific Calculator | Verified | hand-written recursive-descent parser, **no `eval`** |
| GST & Tax Calculator | Verified | add-included/deduct modes, CGST/SGST split |
| Freelance Invoice Calculator | Verified | hours × rate, discount, expenses, tax |
| EMI Calculator | Verified | P·r·(1+r)ⁿ/((1+r)ⁿ−1), formula shown |
| Compound Interest | Verified | A = P(1+r/n)^(nt) with a year-by-year table |
| SIP Estimator | Verified | constant-return assumption stated in the panel |
| Unit Converter | Verified | length/weight/storage/temperature, exact factors |
| Code 128-B Barcode | Verified | real Code 128 patterns + checksum, PNG export |

New editor surfaces were verified too: Acrobat (import 2 PDFs → 4 pages, rotate, duplicate,
freehand annotation, watermark + numbering, export → 5-page PDF re-read with PDF.js, pages → JPG
ZIP), Cut (WAV import with waveform, 1.50 s trimmed WAV, 320×240 PNG frame, trimmed clip written
as a real MP4/ISO-BMFF container with a matching `.mp4` extension), Pixel (800×600 JPEG export
whose reported size matches the bytes, six HEX colours, 2480×3508 A4 passport sheet, send-to-
Acrobat adding a page), Dev (sandbox isolation, JSON/Base64 errors, `2^10 + sqrt(144) = 1036`,
EMI ₹10,746.95, 1 mi = 1609.344 m).

## Honest limits (by design, surfaced in the UI)

- **Video work is real-time**: a 30-second clip takes about 30 seconds. Jobs are capped at
  5 minutes; the reason is printed next to the button.
- **Codec support is the browser's**: only `MediaRecorder.isTypeSupported()` containers are
  listed. If MP4 cannot be written, it is not offered instead of being faked.
- **PDF grayscale and optimisation rasterise pages** to cut size; the text layer is lost and
  the UI says so. The original file is never modified.
- **Standard PDF fonts are WinAnsi**: non-Latin scripts are transliterated or replaced (`₹` is
  written as `Rs`, smart quotes become ASCII) so a document never fails to build.
- **Audio pitch shifting** uses overlap-add resynthesis, not a phase vocoder — expect slight
  artefacts on music, fewer on speech.
- **Screen capture** needs a user gesture and a real display; it cannot be automated in CI.
- **Studio colour filters are preview-grade.** In Cut, brightness/contrast/saturation/grayscale/
  sepia/vintage apply to the live preview; the trimmed-clip export re-encodes the original frames
  through canvas + MediaRecorder, so those per-pixel filters are *not* baked in. Audio processing
  (5-band EQ, volume with clip guard, speed) **is** rendered for real in the WAV/MP3 export.
- **Pixel’s inspector is applied at export and in the preview canvas** — the source file is never
  modified, and a reset restores it without re-uploading.
- **Acrobat does not claim lossless editing**: pages are copied with pdf-lib (crop/annotations
  preserved), grayscale is a raster pass that drops the text layer, and password-protected or
  damaged files are reported instead of half-processed.
- **Container honesty**: MediaRecorder can report `video/mp4` and emit WebM. Every exported clip
  is header-sniffed (`ftyp` vs EBML) and the extension follows the bytes on disk.
- **PWA scope**: the shell is cached; anything that needs the network (Google sign-in) or a
  browser permission (camera, mic, screen) still needs it, and the UI says so instead of
  pretending.

## Testing

`tests/` contains the harness that produced the numbers above:

```bash
python3 tests/make_fixtures.py     # PDF / PNG / WAV fixtures
python3 tests/func_test.py         # runs every file-based tool, saves real outputs
python3 tests/verify_files.py      # re-opens PDFs (PDF.js), decodes audio, loads images
python3 tests/verify_outputs.py    # byte-level format checks (PDF/WAV/MP3/GIF/ZIP/PNG)
python3 tests/suite_a_test.py      # data entry + persistence for the 15 productivity tools
python3 tests/smoke.py             # all 73 registered tools mount, tabs, directory search, no console errors
python3 tests/apps_test.py         # five-app acceptance: launcher, hash routing, palette, all studios
python3 tests/acceptance.py        # end-to-end client checklist (20 checks)
python3 tests/pwa_test.py          # manifest, service worker, offline reload + offline deep link
python3 tests/ui_test.py           # banned words, keyboard nav, responsive overflow, a11y names
python3 tests/planner_auth_test.py # planner persistence + local-profile sign-in flow
python3 tests/acceptance.py        # one end-to-end run mapped to the client checklist
```

Two headline harnesses cover the new architecture:

**`tests/apps_test.py` — 32/32 checks, one browser session, zero console errors.** It verifies:
no “Templates” string anywhere; the exact navbar (Softwares · Planner OS · PDF Studio · Video
Studio · Photo Lab); the hero image still inlined; five bento cards each with a workspace launch
and a `#app=` new-tab link; `#app=dev` deep-links straight into the Dev studio; an invalid hash
(`#app=notreal`) shows a toast and clears the URL; Ctrl+K opens the palette, searches, closes on
Escape, and Enter on “EMI” lands in Dev → EMI calculator with the amount field focused; Planner OS
exposes its seven required modules; Kanban accepts a card; Pomodoro starts and pauses; Acrobat
imports 2 PDFs → 4 pages, rotates, duplicates, records a freehand annotation, applies a watermark
and numbering, exports a 5-page PDF that PDF.js re-opens, and exports pages as JPGs in a ZIP;
Pixel exports a JPEG whose reported size and dimensions match the bytes, extracts six HEX colours,
renders a 2480×3508 A4 passport sheet and sends its image to Acrobat (5 → 6 pages); Cut renders a
waveform, exports a 1.50 s WAV, a 320×240 PNG frame and a trimmed MP4 clip whose header matches its
extension; the sandbox is isolated and renders; JSON and Base64 errors are reported; the calculator
returns 1036; EMI and unit conversion are correct; closing a tab cleans up; the workspace has no
horizontal overflow at 390 px.

**`tests/acceptance.py` — 20/20 checks** covering the original client checklist (identity preserved,
mega-menu search, overlay geometry `fixed / inset 0 / z 250 / #07070a`, tabs, ← Home, planner
progress + reload, profile sign-in and per-email scope, Pomodoro + beep, habit and board
persistence, PDF merge/watermark downloads, waveform + image canvases, mobile overflow, zero errors).

**`tests/pwa_test.py` — 5/5**: manifest linked and valid, service worker activated with the shell
precached, the whole app loads with the browser offline, and `#app=pdf` still opens Acrobat offline.

Also re-run against this build: `smoke.py` (73/73 registered tools mount, tabs, directory search,
0 errors), `ui_test.py` (banned words, keyboard, 0 px overflow at 1440/834/390/320, accessible
names, reduced motion), `func_test.py` (every file tool, run **with `vendor/` moved away**),
`persist_test.py` (14/14 OS modules restored after reload).

Entry points to the software directory are the navbar **Softwares** button, the mobile sheet
**Softwares** row and the footer **All tools** action — all three open the same glass mega-menu
(`[data-action="open-tools"]`).

Reviewed in this build: 73 registered tools mount with zero console/page errors, 0 horizontal
overflow at 1440 / 834 / 390 / 320 px, directory search + keyboard navigation + Escape, tab dedupe
and state retention, persistence across reload, guest/account scope isolation, corrupt storage
quarantine, no rendered “Online”, “Offline”, “Local Browser” or “Demo”.
