function initExpandableForm(toggleId, panelId) {
  const toggle = document.getElementById(toggleId);
  const panel = document.getElementById(panelId);
  if (!toggle || !panel) return;

  panel.removeAttribute("hidden");

  toggle.addEventListener("click", function () {
    const open = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", open ? "false" : "true");
    panel.classList.toggle("is-open", !open);

    if (!open && window.lucide) {
      requestAnimationFrame(function () {
        lucide.createIcons();
      });
    }
  });
}
