(function () {
  const QUEUE_KEY = "moto-offline-queue";
  const banner = document.createElement("div");
  banner.className = "offline-queue-banner";
  banner.setAttribute("role", "status");
  banner.hidden = true;

  function getQueue() {
    try {
      return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
    } catch {
      return [];
    }
  }

  function setQueue(items) {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
    updateBanner();
  }

  function updateBanner() {
    const count = getQueue().length;
    if (!navigator.onLine && count > 0) {
      banner.textContent = count + " entr" + (count === 1 ? "y" : "ies") + " queued — will sync when online";
      banner.hidden = false;
      requestAnimationFrame(function () {
        banner.classList.add("is-visible");
      });
    } else if (count === 0) {
      banner.classList.remove("is-visible", "is-syncing");
      setTimeout(function () {
        if (!getQueue().length) banner.hidden = true;
      }, 400);
    }
  }

  function formToData(form) {
    const data = {};
    new FormData(form).forEach(function (value, key) {
      if (key === "photo" || key === "receipt") return;
      data[key] = value;
    });
    if (form.querySelector("[name=is_partial]")) {
      data.is_partial = form.querySelector("[name=is_partial]").checked;
    }
    return data;
  }

  function enqueue(kind, data) {
    const queue = getQueue();
    queue.push({ kind: kind, data: data, ts: Date.now() });
    setQueue(queue);
  }

  async function syncQueue() {
    const queue = getQueue();
    if (!queue.length || !navigator.onLine) return;

    banner.textContent = "Syncing " + queue.length + " entr" + (queue.length === 1 ? "y" : "ies") + "…";
    banner.hidden = false;
    banner.classList.add("is-visible", "is-syncing");

    try {
      const res = await fetch("/api/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: queue }),
        credentials: "same-origin",
      });
      const result = await res.json();
      if (result.ok) {
        setQueue([]);
        banner.textContent = "Synced " + (result.synced || 0) + " entries";
        banner.classList.remove("is-syncing");
        setTimeout(function () {
          if (!getQueue().length) window.location.reload();
        }, 800);
      }
    } catch (_) {
      banner.classList.remove("is-syncing");
      updateBanner();
    }
  }

  function bindOfflineForms() {
    document.querySelectorAll("form[data-offline-kind]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        if (navigator.onLine) return;

        e.preventDefault();
        const kind = form.getAttribute("data-offline-kind");
        const map = { fuel: "fuel", care: "care" };
        const syncKind = map[kind] || kind;
        if (syncKind !== "fuel" && syncKind !== "care") return;

        enqueue(syncKind, formToData(form));
        form.classList.add("is-success");
        const btn = form.querySelector(".btn-primary");
        if (btn) btn.textContent = "Queued";
        setTimeout(function () {
          form.reset();
          form.classList.remove("is-success");
          if (btn) btn.textContent = "Add";
        }, 1200);
      });
    });
  }

  function bindFormMotion() {
    document.querySelectorAll(".quick-add-form, .fab-sheet-form").forEach(function (form) {
      form.addEventListener("submit", function () {
        if (!navigator.onLine) return;
        form.classList.add("is-submitting");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.body.appendChild(banner);
    bindOfflineForms();
    bindFormMotion();
    updateBanner();
    window.syncOfflineQueue = syncQueue;
    window.addEventListener("online", syncQueue);
    if (navigator.onLine && getQueue().length) syncQueue();
  });
})();
