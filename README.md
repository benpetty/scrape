# scrape

A Python CLI that downloads MP3 tracks from the [Radio Nat Turner](https://www.radionatturner.com) record pool. It logs into each genre page with Selenium, iterates over the embedded audio blocks, and streams every track to disk with a progress bar.

> **Heads up:** this scraper is purpose-built for the Radio Nat Turner site. The selectors (`.password-input`, `.audio-block`, `.title`, `.artistName`, `.secondary-controls .download a`) are specific to that site's markup. It is not a general-purpose scraper.

---

## Features

- Logs into password-protected Radio Nat Turner genre pages via Selenium (Firefox)
- Downloads every track on 11 genre/category pages out of the box
- Skips files that already exist locally (resumable runs)
- Streams downloads in 1 KB chunks with per-file and per-folder progress bars (via [`enlighten`](https://pypi.org/project/enlighten/))
- Backs off and restarts the browser session on HTTP 429 (rate-limited)
- Collects non-429 failures and prints a summary at the end

---

## Requirements

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.12+ | Declared in `pyproject.toml` |
| [`uv`](https://docs.astral.sh/uv/) | latest | Used to manage the venv and run the package |
| Firefox | recent | The scraper drives a real Firefox window |
| `geckodriver` | on `$PATH` | The `Makefile` aborts if it can't find this binary |
| A Radio Nat Turner account | — | You need the site password to log in |

Install everything on macOS:

```bash
brew install uv geckodriver
brew install --cask firefox
```

---

## Installation

```bash
git clone https://github.com/benpetty/scrape.git
cd scrape
make install
# …or, equivalently:
uv sync --extra dev
```

`uv sync` creates a `.venv/` from `pyproject.toml` + `uv.lock`, pinning exact versions for reproducible installs.

---

## Configuration

The scraper reads the site password from the `RADIO_NAT_TURNER_PASSWORD` environment variable. Create a `.env` file at the repo root (it's gitignored):

```bash
# .env
RADIO_NAT_TURNER_PASSWORD=your-password-here
```

The `Makefile` automatically loads and exports `.env`, so `make scrape` will see the variable.

---

## Usage

```bash
make scrape
# …or:
uv run scrape
```

Tracks are saved under `data/<category-slug>/` (gitignored). For example, the `disco` category writes to `data/disco/`.

A run will:

1. Iterate over the 11 hardcoded category URLs in `scrape/radio_nat_turner.py` (`URLS`).
2. Open Firefox, log into each page, and locate every `.audio-block`.
3. Download each track's MP3, skipping anything already on disk.
4. On HTTP 429, close the browser, reopen it, and restart the current category.
5. Print a `💀` summary of any tracks that failed for non-rate-limit reasons.

Press **Ctrl-C** to abort cleanly — the program exits with status `130`.

---

## Project layout

```
scrape/
├── Makefile                       # Wraps install + run; checks for uv + geckodriver
├── pyproject.toml                 # Project metadata, dependencies, entry point
├── uv.lock                        # Pinned dependency tree (committed)
└── scrape/                        # The package
    ├── __init__.py                # Package metadata
    ├── __main__.py                # Entry point (handles KeyboardInterrupt → exit 130)
    ├── radio_nat_turner.py        # Main scraper: URLs, login, downloads, retries
    └── core/
        ├── exit_status.py         # IntEnum of exit codes
        ├── normalize_filename.py  # strip_accents() helper
        └── progress_bars.py       # enlighten wrapper with named color formats
```

---

## How it works

1. **`scrape/__main__.py`** is the entry point (`uv run scrape` → `python -m scrape`). It wraps the run in a `try/except KeyboardInterrupt` so Ctrl-C produces exit code 130.
2. **`RadioNatTurner(url).scrape()`** in `radio_nat_turner.py`:
   - Spawns a Firefox WebDriver (Selenium 4 auto-resolves `geckodriver` via Selenium Manager if not on `$PATH`).
   - Visits the URL, types the password into `.password-input`, and presses Return.
   - Waits for `.audio-block` elements to render.
   - For each block, pulls the title, artist, and download URL, then either skips (already on disk) or streams the MP3.
3. **`Writer`** is a context manager that wraps each download: it opens the destination file, attaches an `enlighten` progress counter, and writes the response stream in 1 KB chunks.
4. **Rate-limit handling** — on `429 Too Many Requests`, the scraper closes the browser, spawns a fresh one, and recursively re-invokes `scrape()` for the same category. There is no backoff or attempt cap, so a persistently rate-limited category can loop indefinitely; interrupt with Ctrl-C if that happens.
5. **Other failures** are collected in a module-level `FAILURES` list and printed at the end of the run as a `💀` summary block.

---

## Known limitations

- **No retry cap on 429** — see "How it works" above.
- **Empty password** is silently allowed: `os.environ.get("RADIO_NAT_TURNER_PASSWORD")` returns `None` if the env var is missing, and the login submits nothing.
- **`scrape/core/normalize_filename.py`** is currently unused. Accented track-title filenames pass through unchanged.

---

## License

MIT — see package metadata in `pyproject.toml`.
