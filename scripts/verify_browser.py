#!/usr/bin/env python3
"""Browser checks and fresh screenshots for the static site (requires Playwright)."""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(color_scheme="light")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: errors.append(f"HTTP {response.status}: {response.url}")
                if response.status >= 400 else None)
        page.goto(args.base_url)
        assert page.locator("html").get_attribute("data-theme") == "dark"
        assert page.locator(".research-item").count() == 3
        assert page.locator(".project-link").count() == 3
        for theme in ("dark", "light"):
            page.get_by_role("switch", name="Dark mode").set_checked(theme == "dark")
            for width in (320, 360, 480, 481, 640, 768, 769, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (theme, width)
                columns = page.locator(".research-grid").evaluate(
                    "el => getComputedStyle(el).gridTemplateColumns.split(' ').length")
                assert columns == (1 if width <= 768 else 3), (theme, width, columns)
                for link in page.locator(".project-link").all():
                    assert link.is_visible()
                if width in (360, 768, 1440):
                    prefix = "verification-light" if theme == "light" else "verification"
                    page.screenshot(path=str(root / f"{prefix}-{width}.png"), full_page=True)
                print(f"PASS layout: {theme}, {width}px")
        page.reload()
        assert page.locator("html").get_attribute("data-theme") == "light"
        switch = page.get_by_role("switch", name="Dark mode")
        switch.focus()
        page.keyboard.press("Space")
        assert switch.is_checked()
        page.reload()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        for label, fragment in (("About", "about"), ("Research", "research"), ("Approach", "approach")):
            page.get_by_role("navigation", name="Main navigation").get_by_role("link", name=label, exact=True).click()
            assert page.url.endswith("#" + fragment)
        page.get_by_role("link", name="Explore the projects").click()
        assert page.url.endswith("#research")
        page.get_by_role("link", name="WYŁOM Research, back to top").click()
        assert page.url.endswith("#top")
        page.goto(args.base_url)
        page.keyboard.press("Tab")
        assert page.locator(".skip-link").evaluate("el => el === document.activeElement")
        page.keyboard.press("Enter")
        assert page.locator("#main").evaluate("el => el === document.activeElement")
        page.goto(args.base_url.rstrip("/") + "/#research")
        page.reload()
        assert page.url.endswith("#research")
        no_js = browser.new_context(java_script_enabled=False)
        fallback = no_js.new_page()
        fallback.goto(args.base_url)
        assert fallback.locator("html").get_attribute("data-theme") == "dark"
        assert not fallback.locator(".theme-control").is_visible()
        assert fallback.get_by_role("heading", name="Selected projects").is_visible()
        no_js.close()
        assert not errors, errors
        context.close()
        browser.close()
    print("PASS browser: navigation, skip link, pointer/keyboard themes, persistence, no-JS fallback, no page/HTTP errors")


if __name__ == "__main__":
    main()
