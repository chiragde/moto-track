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

  async function subscribePush() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) return false;

    try {
      const keyRes = await fetch("/api/vapid-public-key");
      const { publicKey } = await keyRes.json();
      if (!publicKey) return false;

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
      await fetch("/api/push-subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sub.toJSON()),
        credentials: "same-origin",
      });
      return true;
    } catch (_) {
      return false;
    }
  }

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const raw = atob(base64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    return arr;
  }

  window.requestMotoNotifications = async function () {
    if (!("Notification" in window)) {
      alert("Notifications are not supported in this browser.");
      return false;
    }
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      await subscribePush();
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

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.addEventListener("message", function (e) {
        if (e.data && e.data.type === "SYNC_QUEUE" && window.syncOfflineQueue) {
          window.syncOfflineQueue();
        }
      });
    }
  });
})();
