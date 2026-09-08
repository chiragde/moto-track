(function () {
  const liters = document.getElementById("liters");
  const cost = document.getElementById("cost");
  const priceEl = document.getElementById("price-per-liter");
  if (!liters || !cost || !priceEl) return;

  function update() {
    const l = parseFloat(liters.value);
    const c = parseFloat(cost.value);
    if (l > 0 && c >= 0) {
      priceEl.textContent = (c / l).toFixed(2);
      priceEl.parentElement.hidden = false;
    } else {
      priceEl.parentElement.hidden = true;
    }
  }

  liters.addEventListener("input", update);
  cost.addEventListener("input", update);
})();
