window.motoHaptic = function (type) {
  if (!navigator.vibrate) return;
  const patterns = { light: 8, medium: 15, success: [10, 40, 10] };
  navigator.vibrate(patterns[type] || 8);
};

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      window.motoHaptic("light");
    });
  });
  document.querySelectorAll(".btn-primary").forEach(function (btn) {
    btn.addEventListener("click", function () {
      window.motoHaptic("light");
    });
  });
});
