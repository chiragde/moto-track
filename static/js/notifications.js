(function () {
  async function checkReminders() {
    if (!("Notification" in window)) return;
    if (Notification.permission !== "granted") return;

    try {
      const res = await fetch("/api/due-reminders");
      const data = await res.json();
      if (!data.due || !data.due.length) return;

      data.due.forEach(function (item) {
        new Notification("Moto Track — " + item.title, {
          body: item.detail || "Maintenance reminder",
          icon: "/static/icons/icon.svg",
          tag: "reminder-" + item.title,
        });
      });
    } catch (_) {}
  }

  window.requestMotoNotifications = async function () {
    if (!("Notification" in window)) {
      alert("Notifications are not supported in this browser.");
      return false;
    }
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      checkReminders();
      return true;
    }
    return false;
  };

  document.addEventListener("DOMContentLoaded", function () {
    const enableBtn = document.getElementById("enable-notifications");
    if (enableBtn) {
      enableBtn.addEventListener("click", window.requestMotoNotifications);
    }
    if (Notification.permission === "granted") {
      checkReminders();
    }
  });
})();
