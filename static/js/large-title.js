(function () {
  const title = document.querySelector(".large-title");
  const topBar = document.querySelector(".top-bar");
  if (!title || !topBar) return;

  const onScroll = function () {
    const y = window.scrollY;
    title.classList.toggle("is-collapsed", y > 24);
    topBar.classList.toggle("is-scrolled", y > 4);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
