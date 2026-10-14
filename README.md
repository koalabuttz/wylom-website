# WYŁOM Research website

The static website for WYŁOM Research, David's independent research practice in Cambridge, exploring cybersecurity, AI agents, and networking.

Built with semantic HTML, responsive CSS, and a small JavaScript theme switch. No framework, external fonts, analytics, backend, or build step.

## Preview locally

From the repository directory:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/. Stop the server with Ctrl+C. If the port is occupied, choose another port and use it in the check commands below.

## Files

- `index.html` — page content, metadata, navigation, and public project links.
- `styles.css` — responsive layout, light/dark palettes, and focus styles.
- `theme.js` — theme selection and saved preferences.
- `scripts/verify_site.py` — standard-library source, HTTP, and screenshot checks.
- `scripts/verify_browser.py` — optional Playwright browser checks and screenshot generation.

The site links to public research and software projects. AOS is described as architecture research, not a working operating system. Project descriptions are not independent runtime validation of the linked software.

## Checks

No extra Python dependencies are needed for source and HTTP checks:

```sh
python3 scripts/verify_site.py sources --root .
python3 scripts/verify_site.py http --root . --base-url http://127.0.0.1:8000/
```

Start the preview server before the HTTP check.

For optional browser checks, install Playwright in a local environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install playwright
python -m playwright install chromium
python3 scripts/verify_browser.py --base-url http://127.0.0.1:8000/
python3 scripts/verify_site.py artifacts --root .
```

Linux may need browser system dependencies installed; see the [Playwright installation documentation](https://playwright.dev/python/docs/intro).

The browser checks cover both themes at eight widths from 320 to 1440 CSS pixels, internal navigation, the keyboard skip link, theme switching and persistence, and JavaScript-disabled rendering. They generate six full-page `verification-*.png` screenshots. These screenshots and local verification notes are intentionally ignored by Git. Run the browser checks before the artifact check on a fresh clone.

Screenshot integrity checks do not establish visual correctness. Review screenshots manually after layout changes. Actual browser-toolbar zoom, exhaustive browser compatibility, and external project software are outside the automated checks.

## Theme and navigation

Fresh visits start in dark mode. The native Dark mode switch works with pointer or keyboard and remembers an explicit selection in browser-local storage under `wylom-theme`. Without JavaScript, the page remains readable in dark mode and the inactive switch stays hidden.

About, Research, and Approach link to page sections. The wordmark returns to the top, and a keyboard skip link targets the main content. Project and profile links open in the same tab.

## Publish

Deploy only these three files, together in the same directory:

```text
index.html
styles.css
theme.js
```

Any static host can serve them. There is no build command and no server-side runtime. If your host publishes the repository root, it may also expose repository documentation and scripts; use a publish directory containing only the three site files when possible.

A GitHub Pages deployment from `main` and `/ (root)` works without a build step. It also makes other tracked root files accessible, so use a dedicated deployment directory or workflow if you want to publish only the site assets. No custom domain is configured in this repository.

## Contributing

Corrections and small improvements are welcome through issues or pull requests. Keep the site dependency-free, preserve keyboard navigation and the JavaScript-disabled fallback, and check both narrow and wide layouts in both themes.

## License

The site code and technical repository documentation are licensed under [MIT](LICENSE). The website's editorial copy, logos, and brand artwork are not covered by that license. No trademark rights in the WYŁOM Research name or branding are granted. Replace the branding and editorial copy if you reuse the code for another site.
