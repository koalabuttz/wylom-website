(() => {
  "use strict";

  const storageKey = "wylom-theme";
  const themeColors = { dark: "#101613", light: "#f7f7f2" };

  function readPreferredTheme() {
    try {
      const saved = window.localStorage.getItem(storageKey);
      return saved === "light" || saved === "dark" ? saved : "dark";
    } catch {
      return "dark";
    }
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    const metadata = document.querySelector('meta[name="theme-color"]');
    if (metadata) {
      metadata.content = themeColors[theme];
    }
    const toggle = document.getElementById("theme-toggle");
    if (toggle) {
      toggle.checked = theme === "dark";
    }
  }

  function savePreferredTheme(theme) {
    try {
      window.localStorage.setItem(storageKey, theme);
    } catch {
      // Storage restrictions must not prevent switching for this visit.
    }
  }

  function initializeThemeControl() {
    const toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    applyTheme(document.documentElement.dataset.theme);
    toggle.addEventListener("change", () => {
      const theme = toggle.checked ? "dark" : "light";
      applyTheme(theme);
      savePreferredTheme(theme);
    });
    toggle.closest(".theme-control").hidden = false;
  }

  // Restore a choice before the stylesheet paints; a fresh visit stays dark.
  applyTheme(readPreferredTheme());
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeThemeControl, { once: true });
  } else {
    initializeThemeControl();
  }
})();
