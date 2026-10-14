#!/usr/bin/env python3
"""Read-only acceptance checks for the WYŁOM Research static website."""

import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import struct
import sys
from urllib.error import URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import urlopen
import zlib


class CheckFailure(Exception):
    """An acceptance predicate failed or a required resource is unavailable."""


def require(condition, message):
    if not condition:
        raise CheckFailure(message)


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise CheckFailure(f"{path}: {error}") from error


class SiteDocument(HTMLParser):
    """Collect document structure and visible text without executing content."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.ids = []
        self.fragments = []
        self.visible = []
        self.title = []
        self.heading = []
        self.doctype = False
        self.in_title = False
        self.in_heading = False
        self.hidden_depth = 0

    def handle_decl(self, declaration):
        self.doctype = self.doctype or declaration.lower() == "doctype html"

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.elements.append((tag, attrs))
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.fragments.append(unquote(attrs["href"][1:]))
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_heading = True
        if tag in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_heading = False
        if tag in {"script", "style"}:
            self.hidden_depth = max(0, self.hidden_depth - 1)

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        elif not self.hidden_depth:
            self.visible.append(data)
        if self.in_heading:
            self.heading.append(data)

    def tagged(self, tag):
        return [attrs for name, attrs in self.elements if name == tag]


def normalized(parts):
    return " ".join("".join(parts).split())


def check_sources(root):
    html = read_text(root / "index.html")
    css = read_text(root / "styles.css")
    readme = read_text(root / "README.md")
    document = SiteDocument()
    document.feed(html)
    document.close()
    require(document.doctype, "index.html: missing HTML doctype")
    require(any(a.get("lang") == "en" for a in document.tagged("html")),
            "index.html: document language must be en")
    metadata = document.tagged("meta")
    require(any(a.get("charset", "").lower() == "utf-8" for a in metadata),
            "index.html: missing UTF-8 declaration")
    viewport = next((a.get("content", "") for a in metadata
                     if a.get("name") == "viewport"), "")
    require("width=device-width" in viewport and "initial-scale=1" in viewport,
            "index.html: missing responsive viewport metadata")
    description = next((a.get("content", "") for a in metadata
                        if a.get("name") == "description"), "")
    for phrase in ("WYŁOM Research", "independent", "Cambridge",
                   "cybersecurity", "AI agents", "networking"):
        require(phrase in description, f"index.html: description missing {phrase!r}")
    require("WYŁOM Research" in normalized(document.title),
            "index.html: title must preserve WYŁOM Research")
    require(len(document.tagged("h1")) == 1, "index.html: expected one h1")
    require(normalized(document.heading) == "WYŁOM Research",
            "index.html: h1 must preserve WYŁOM Research")
    visible = normalized(document.visible).lower()
    for phrase in ("independent research practice", "david", "cambridge",
                   "cybersecurity", "ai agents", "networking",
                   "increasingly autonomous software", "understand and control",
                   "we move between the two", "selected projects",
                   "aos", "not a working os", "prompt64", "commodore 64",
                   "tailscale-vita", "playstation vita"):
        require(phrase in visible, f"index.html: visible content missing {phrase!r}")
    projects = [attrs for tag, attrs in document.elements if tag == "article"
                and "research-item" in attrs.get("class", "").split()]
    require(len(projects) == 3, "index.html: expected three selected projects")
    external_links = {a.get("href") for a in document.tagged("a")}
    for destination in ("https://tangled.org/david.boston/AOS",
                        "https://tangled.org/david.boston/prompt64",
                        "https://github.com/koalabuttz/tailscale-vita",
                        "https://tangled.org/david.boston",
                        "https://github.com/koalabuttz"):
        require(destination in external_links,
                f"index.html: missing public project/profile link {destination}")
    duplicates = [value for value, count in Counter(document.ids).items() if count > 1]
    require(not duplicates, f"index.html: duplicate IDs: {duplicates}")
    for destination in document.fragments:
        require(destination in document.ids,
                f"index.html: missing fragment destination #{destination}")
    for destination in ("top", "main", "about", "research", "approach"):
        require(destination in document.fragments,
                f"index.html: missing navigation link to #{destination}")
    require(any(a.get("id") == "main" and a.get("tabindex") == "-1"
                for a in document.tagged("main")),
            "index.html: main must be a focusable skip-link destination")
    stylesheets = [a for a in document.tagged("link")
                   if "stylesheet" in a.get("rel", "").split()]
    require(len(stylesheets) == 1 and stylesheets[0].get("href") == "./styles.css",
            "index.html: expected the relative ./styles.css stylesheet")
    require(bool(css.strip()), "styles.css: stylesheet is empty")
    roots = document.tagged("html")
    require(len(roots) == 1 and roots[0].get("data-theme") == "dark",
            "index.html: default theme must be dark")
    theme_metadata = [a for a in metadata if a.get("name") == "theme-color"]
    require(len(theme_metadata) == 1
            and theme_metadata[0].get("content") == "#101613",
            "index.html: initial theme-color must be #101613")
    toggles = [a for a in document.tagged("input")
               if a.get("id") == "theme-toggle"]
    require(len(toggles) == 1 and toggles[0].get("type") == "checkbox"
            and toggles[0].get("role") == "switch"
            and toggles[0].get("aria-label") == "Dark mode"
            and "checked" in toggles[0],
            "index.html: theme-toggle must be a checked Dark mode checkbox switch")
    controls = [a for a in document.tagged("label")
                if "theme-control" in a.get("class", "").split()]
    require(len(controls) == 1 and "hidden" in controls[0],
            "index.html: theme-control must initially be hidden")
    scripts = document.tagged("script")
    require(len(scripts) == 1 and scripts[0].get("src") == "./theme.js"
            and "async" not in scripts[0] and "defer" not in scripts[0],
            "index.html: expected synchronous relative ./theme.js script")
    script_index = next(i for i, (tag, attrs) in enumerate(document.elements)
                        if tag == "script" and attrs.get("src") == "./theme.js")
    stylesheet_index = next(i for i, (tag, attrs) in enumerate(document.elements)
                            if tag == "link" and attrs.get("href") == "./styles.css")
    require(script_index < stylesheet_index,
            "index.html: theme.js must precede styles.css")
    require(bool(read_text(root / "theme.js").strip()), "theme.js: script is empty")
    for command in ("python3 -m http.server 8000 --bind 127.0.0.1",
                    "python3 scripts/verify_site.py sources --root .",
                    "python3 scripts/verify_site.py http --root . --base-url http://127.0.0.1:8000/",
                    "python3 scripts/verify_site.py artifacts --root ."):
        require(command in readme, f"README.md: missing command {command!r}")
    print("PASS sources: UTF-8, metadata, research content, headings, IDs, links, theme structure, and commands")


def check_http(root, base_url):
    parsed = urlsplit(base_url)
    require(parsed.scheme in {"http", "https"} and bool(parsed.netloc)
            and not parsed.query and not parsed.fragment,
            f"HTTP base URL is invalid: {base_url}")
    for name, relative in (("index.html", "./"),
                           ("styles.css", "styles.css"),
                           ("theme.js", "theme.js")):
        path = root / name
        expected = path.read_bytes()
        url = urljoin(base_url.rstrip("/") + "/", relative)
        try:
            with urlopen(url, timeout=5) as response:
                require(response.status == 200, f"{url}: expected HTTP 200")
                actual = response.read(len(expected) + 1)
        except (URLError, OSError, ValueError) as error:
            raise CheckFailure(f"{url}: {error}") from error
        require(actual == expected, f"{url}: response differs from current {path}")
        print(f"PASS HTTP: {url} matches {name} ({len(expected)} bytes)")


def png_dimensions(path):
    """Validate bounded PNG chunks and CRCs; appearance needs browser review."""
    require(path.stat().st_size <= 32 * 1024 * 1024, f"{path}: PNG exceeds 32 MiB")
    with path.open("rb") as stream:
        require(stream.read(8) == b"\x89PNG\r\n\x1a\n", f"{path}: invalid PNG signature")
        dimensions = None
        saw_data = False
        data_finished = False
        for index in range(10000):
            header = stream.read(8)
            require(len(header) == 8, f"{path}: truncated PNG chunk header")
            length, kind = struct.unpack(">I4s", header)
            require(length <= 32 * 1024 * 1024, f"{path}: oversized PNG chunk")
            require(all(65 <= byte <= 90 or 97 <= byte <= 122 for byte in kind),
                    f"{path}: invalid PNG chunk type")
            data = stream.read(length)
            checksum = stream.read(4)
            require(len(data) == length and len(checksum) == 4,
                    f"{path}: truncated {kind!r} chunk")
            require(zlib.crc32(kind + data) & 0xffffffff == struct.unpack(">I", checksum)[0],
                    f"{path}: invalid {kind!r} CRC")
            require(index != 0 or kind == b"IHDR", f"{path}: IHDR must be first")
            if kind == b"IHDR":
                require(dimensions is None and length == 13, f"{path}: invalid IHDR")
                width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
                allowed_depths = {0: {1, 2, 4, 8, 16}, 2: {8, 16},
                                  3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
                require(width > 0 and height > 0 and depth in allowed_depths.get(color, set())
                        and compression == 0 and filtering == 0 and interlace in {0, 1},
                        f"{path}: unsupported or invalid IHDR fields")
                dimensions = (width, height)
            elif kind == b"IDAT":
                require(not data_finished, f"{path}: nonconsecutive IDAT chunks")
                saw_data = True
            elif kind == b"IEND":
                require(length == 0 and saw_data and dimensions is not None,
                        f"{path}: invalid IEND or missing image data")
                require(not stream.read(1), f"{path}: bytes after IEND")
                return dimensions
            elif saw_data:
                data_finished = True
        raise CheckFailure(f"{path}: PNG chunk count exceeds 10000")


def check_artifacts(root):
    captures = {
        "verification-360.png": 360,
        "verification-768.png": 768,
        "verification-1440.png": 1440,
        "verification-light-360.png": 360,
        "verification-light-768.png": 768,
        "verification-light-1440.png": 1440,
    }
    for name, width in captures.items():
        path = root / name
        actual_width, height = png_dimensions(path)
        require(actual_width == width, f"{path}: expected width {width}, got {actual_width}")
        print(f"PASS artifact: {path.name}, {actual_width} x {height}, valid PNG chunks and CRCs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("sources", "http", "artifacts"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, default=Path("."))
        if name == "http":
            command.add_argument("--base-url", required=True)
    args = parser.parse_args()
    try:
        if args.command == "sources":
            check_sources(args.root)
        elif args.command == "http":
            check_http(args.root, args.base_url)
        else:
            check_artifacts(args.root)
    except (CheckFailure, OSError, UnicodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
