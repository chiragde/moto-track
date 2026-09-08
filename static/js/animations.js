(function () {
  const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const NAV_KEY = "moto-nav-transition";
  const ORIGIN_KEY = "moto-anim-origin";

  const STAGGER_SELECTOR =
    ".content > .flash, .content > .bike-selector, .content > .stat-grid, " +
    ".content > .stat-card, .content > .card, .content > .tip-card, .content > .empty-state, " +
    ".home-hero, .home-glance, .home-milestone, .home-actions, .home-reminders";

  function setTransition(type, origin) {
    if (REDUCED_MOTION) {
      return;
    }
    sessionStorage.setItem(NAV_KEY, type);
    if (origin) {
      sessionStorage.setItem(ORIGIN_KEY, JSON.stringify(origin));
    }
  }

  function getOriginFromElement(el) {
    const rect = el.getBoundingClientRect();
    return {
      x: Math.round(rect.left + rect.width / 2),
      y: Math.round(rect.top + rect.height / 2),
    };
  }

  function getActiveTabOrigin() {
    const active = document.querySelector(".bottom-nav .nav-item.active");
    if (active) {
      return getOriginFromElement(active);
    }
    const nav = document.querySelector(".bottom-nav");
    if (nav) {
      return getOriginFromElement(nav);
    }
    return { x: window.innerWidth / 2, y: window.innerHeight - 40 };
  }

  function applyPageOrigin(origin) {
    document.documentElement.style.setProperty("--anim-origin-x", origin.x + "px");
    document.documentElement.style.setProperty("--anim-origin-y", origin.y + "px");
  }

  function applyStaggeredOrigins(origin) {
    const items = document.querySelectorAll(STAGGER_SELECTOR);
    items.forEach(function (el, index) {
      const rect = el.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const pull = 0.28;
      const tx = (origin.x - cx) * pull;
      const ty = (origin.y - cy) * pull;

      el.style.setProperty("--enter-tx", tx + "px");
      el.style.setProperty("--enter-ty", ty + "px");
      el.style.setProperty("--enter-delay", (0.12 + index * 0.08) + "s");
      el.classList.add("animate-from-origin");
    });
  }

  function applyEntryTransition() {
    const type = sessionStorage.getItem(NAV_KEY) || "none";
    sessionStorage.removeItem(NAV_KEY);

    let origin = null;
    try {
      origin = JSON.parse(sessionStorage.getItem(ORIGIN_KEY) || "null");
    } catch {
      origin = null;
    }
    sessionStorage.removeItem(ORIGIN_KEY);

    if (type === "none") {
      if (document.querySelector(".auth-page")) {
        document.body.classList.add("nav-auth");
      }
      return;
    }

    if (!origin) {
      origin = getActiveTabOrigin();
    }

    applyPageOrigin(origin);
    document.body.classList.add("nav-" + type);

    requestAnimationFrame(function () {
      applyStaggeredOrigins(origin);
    });
  }

  function isInternalLink(anchor) {
    if (!anchor.href) {
      return false;
    }
    try {
      const url = new URL(anchor.href, window.location.origin);
      return url.origin === window.location.origin && url.pathname !== window.location.pathname;
    } catch {
      return false;
    }
  }

  function isTabLink(anchor) {
    return anchor.closest(".bottom-nav") !== null;
  }

  function isBackLink(anchor) {
    return anchor.classList.contains("top-bar-back") || anchor.classList.contains("nav-back");
  }

  document.addEventListener("click", function (event) {
    const anchor = event.target.closest("a[href]");
    if (!anchor || anchor.target === "_blank" || anchor.hasAttribute("download")) {
      return;
    }
    if (!isInternalLink(anchor)) {
      return;
    }

    const origin = getOriginFromElement(anchor);

    if (isBackLink(anchor)) {
      setTransition("back", origin);
      return;
    }
    if (isTabLink(anchor)) {
      setTransition("tab", origin);
      return;
    }
    setTransition("forward", origin);
  });

  document.addEventListener("DOMContentLoaded", function () {
    applyEntryTransition();

    const topBar = document.querySelector(".top-bar");
    const content = document.querySelector(".content");
    if (topBar && content) {
      const onScroll = function () {
        topBar.classList.toggle("is-scrolled", content.scrollTop > 4 || window.scrollY > 4);
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }

    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function () {
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          submitBtn.style.transform = "scale(0.97)";
          submitBtn.style.opacity = "0.85";
        }
      });
    });
  });
})();
