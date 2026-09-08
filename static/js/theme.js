(function () {
  const root = document.documentElement;
  const META_COLOR = { light: "#007aff", dark: "#0a84ff" };

  function resolve(theme) {
    if (theme === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return theme;
  }

  function apply(pref) {
    const resolved = resolve(pref);
    root.setAttribute("data-theme", resolved);
    root.setAttribute("data-theme-pref", pref);

    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", META_COLOR[resolved] || META_COLOR.light);
    }
  }

  function readServerPref() {
    return root.getAttribute("data-theme-pref");
  }

  function init() {
    const serverPref = readServerPref();
    const stored = localStorage.getItem("moto-theme");
    const pref = serverPref || stored || "system";

    apply(pref);
    localStorage.setItem("moto-theme", pref);
  }

  init();

  window.setMotoTheme = function (theme) {
    localStorage.setItem("moto-theme", theme);
    root.setAttribute("data-theme-pref", theme);
    apply(theme);
  };

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    const pref = readServerPref() || localStorage.getItem("moto-theme") || "system";
    if (pref === "system") {
      apply("system");
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    const serverPref = readServerPref();
    if (serverPref) {
      localStorage.setItem("moto-theme", serverPref);
      apply(serverPref);
    }
  });
})();
