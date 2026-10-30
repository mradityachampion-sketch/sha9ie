#!/usr/bin/env python3
"""
Build: src/{index.template.html, styles.css, app.js} + css/workspace.css
       + js/*.js + assets/fonts  ->  index.html

index.html is the single entry point. Everything first-party (design system,
homepage app, workspace shell, all 55 tools, the GIF encoder) is inlined so the
page has zero network requests and opens straight from disk.

Third-party libraries are NOT inlined - they are loaded lazily from ./vendor/
only when a tool that needs them is opened:

  vendor/pdf-lib.min.js        pdf-lib 1.17.1        MIT
  vendor/pdf.min.js            pdf.js 3.11.174       Apache-2.0
  vendor/pdf.worker.min.js     pdf.js worker 3.11.174 Apache-2.0
  vendor/jszip.min.js          JSZip 3.10.1          MIT
  vendor/lame.min.js           lamejs 1.2.1          LGPL-3.0
  vendor/qrcode.js             qrcode-generator 1.4.4 MIT

The third-party libraries are EMBEDDED by default so index.html is a genuine
single file: each one is base64-encoded into an inert
<script type="text/plain" id="sha-vendor-*"> tag and only decoded + executed
when a tool that needs it is opened. Pass --external-vendor to emit the same
page but load them from ./vendor/ at runtime instead (smaller HTML, needs the
folder next to index.html).

Run:
  python3 build.py                  # single self-contained file
  python3 build.py --external-vendor
"""
from pathlib import Path
import base64
import re
import sys

ROOT = Path(__file__).parent
SRC = ROOT / "src"
IMG = ROOT / "assets" / "hero-field-opt.jpg"
FONT_CSS = ROOT / "fonts" / "inline.css"

# first-party modules, in load order (each defines/extends window.SHA)
JS_FILES = [
    "js/core.js",
    "js/lib/gif.js",
    "js/workspace.js",
    "js/apps.js",          # five apps, launcher, hash routing, pipe, commands
    "js/palette.js",       # Ctrl/Cmd+K command palette
    "js/studios.js",       # studio shell (a tab per application)
    "js/studio-acrobat.js",
    "js/studio-cut.js",
    "js/studio-pixel.js",
    "js/tools-a.js",
    "js/tools-b.js",
    "js/tools-c.js",
    "js/tools-d.js",       # developer + calculator tools
]

EXTERNAL_VENDOR = "--external-vendor" in sys.argv

# name in the HTML  ->  vendor file
VENDOR = [
    ("pdf-lib", "vendor/pdf-lib.min.js"),
    ("pdfjs", "vendor/pdf.min.js"),
    ("pdfjs-worker", "vendor/pdf.worker.min.js"),
    ("jszip", "vendor/jszip.min.js"),
    ("lame", "vendor/lame.min.js"),
    ("qrcode", "vendor/qrcode.js"),
]

hero_data_uri = 'url("data:image/jpeg;base64,' + base64.b64encode(IMG.read_bytes()).decode() + '")'

html = (SRC / "index.template.html").read_text()
styles = (SRC / "styles.css").read_text().replace("__HERO_IMG__", hero_data_uri)
ws_styles = (ROOT / "css" / "workspace.css").read_text()
app_js = (SRC / "app.js").read_text()

fonts = FONT_CSS.read_text().strip()

ws_js_parts = []
for rel in JS_FILES:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"missing module: {rel}")
    ws_js_parts.append(f"/* ---- {rel} ---- */\n" + path.read_text())
ws_js = "\n".join(ws_js_parts)

vendor_html = ""
vendor_bytes = 0
if not EXTERNAL_VENDOR:
    parts = []
    for name, rel in VENDOR:
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"missing vendor file: {rel}")
        raw = path.read_bytes()
        vendor_bytes += len(raw)
        b64 = base64.b64encode(raw).decode()
        # base64 cannot contain "<", so </script> can never appear here
        parts.append(
            f'<script type="text/plain" id="sha-vendor-{name}" data-bytes="{len(raw)}">'
            + b64
            + "</script>"
        )
    vendor_html = "\n".join(parts)

html = html.replace("<!--{{VENDOR}}-->", vendor_html)
html = html.replace("/*{{FONTS}}*/", fonts)
html = html.replace("/*{{STYLES}}*/", styles)
html = html.replace("/*{{WS_STYLES}}*/", ws_styles)
html = html.replace("/*{{APP_JS}}*/", app_js)
html = html.replace("/*{{WS_JS}}*/", ws_js)

leftovers = re.findall(r"\{\{[A-Z_]+\}\}", html)
if leftovers:
    raise SystemExit(f"Unresolved placeholders: {set(leftovers)}")

# a closing </script> inside an inlined string would end the script block early
for frag in ("</script", "<!--"):
    if frag in ws_js or frag in app_js:
        raise SystemExit(f"Unsafe sequence {frag!r} inside inlined JS")

(ROOT / "index.html").write_text(html)

tools = len(re.findall(r'S\.register\(\{', ws_js))
print(f"index.html written - {len(html)/1024:.0f} KB")
print(f"inline modules: {', '.join(JS_FILES)}")
print(f"registered tool definitions: {tools}")
if EXTERNAL_VENDOR:
    print("third-party libs: loaded lazily from ./vendor/ (folder must ship with index.html)")
else:
    print(f"third-party libs: embedded ({vendor_bytes/1024/1024:.2f} MB raw, base64 in-file, decoded on demand)")
