# mhscraper

A **one‑file, one‑level scraper** that turns a web page (or a list of URLs) into
Markdown files with YAML front‑matter.

* **Language‑agnostic:** any site, any sub‑domain.
* **Single hop:** crawls only the links that stay on the same sub‑domain
  (or takes URLs you supply in a file).
* **Front‑matter:** title, date, optional author, and source link.
* **Fast setup:** uses the `uv` tool for ultra‑quick virtual‑envs + installs.

---

## What it does

1. **Collect URLs**

   | Scenario | What happens |
   |----------|--------------|
   | `urls.txt` exists & not empty | Every non‑blank line is a URL to scrape. |
   | `urls.txt` missing/empty + `start_url` argument | Fetches the page and grabs every `<a>` that resolves to the *same sub‑domain* (duplicates removed). |

2. **Download each page** (`requests`).

3. **Extract the main article** (`readability‑lxml`).

4. **Convert HTML → Markdown** (`markdownify`).

5. **Add YAML front‑matter**

   ```yaml
   ---
   title: "Post title"
   date: 2025-04-22
   # author: Your Name            # only present if you pass --author
   source: https://example.com/2025/04/post-slug
   ---
   ```

6. **Save the file** to `posts_md/YYYY-MM-DD-post-slug.md` (folder configurable).

---

## Quick start

```bash
git clone https://github.com/techczech/mhscraper.git
cd mhscraper

# one‑time tool install
brew install uv

# create env & deps
uv venv .venv
uv pip install 'lxml[html_clean]' requests readability-lxml markdownify \
              python-slugify beautifulsoup4

# 1) crawl one page for same‑domain links
uv run grab_posts.py https://example.com

# 2) OR scrape links listed in urls.txt
uv run grab_posts.py -f urls.txt

# add an author field
uv run grab_posts.py https://example.com --author "Alice Example"
```

---

## CLI options

| Option | Default | Purpose |
|--------|---------|---------|
| `start_url` | — | Page whose same‑domain links will be scraped (ignored if `--file` is non‑empty). |
| `-f, --file` | `urls.txt` | Text file with one URL per line. |
| `-o, --out` | `posts_md` | Output folder. |
| `--delay` | `1.0` | Seconds to wait between requests. |
| `--author` | *(none)* | Author name to include in front‑matter. |

Run `uv run grab_posts.py -h` for full help.

---

## Files

| Path | Purpose |
|------|---------|
| `grab_posts.py` | ~150 lines; the entire scraper. |
| `urls.txt` | *(optional)* List of URLs to scrape. |
| `posts_md/` | Output Markdown (created on first run). |

---

## Customising

* **Different crawl depth** → modify `collect_urls()` logic.
* **Front‑matter fields** → edit `make_front_matter()` (near bottom of script).
* **Selector/regex** tweaks → also in `collect_urls()`.

---

## Why uv?

* **Rust‑powered speed** for both env creation and package installs.
* Single binary replaces `python -m venv`, `pip`, and `pip‑tools`.
* Plays nicely with Homebrew’s PEP 668 protection—no global pollution.

---

## License

MIT – see `LICENSE`.