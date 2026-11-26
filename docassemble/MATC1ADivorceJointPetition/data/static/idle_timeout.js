// Shared-device idle time-out (1A #213). After the idle limit in
// #al-idle-settings (minutes), show a warning; with no answer for 60 more
// seconds, follow the quick-exit link, which ends the session.
(function () {
  if (window.alIdleTimeoutLoaded) { return; }
  window.alIdleTimeoutLoaded = true;
  window.alIdleLastActivity = Date.now();
  window.alIdleWarningAt = null;
  var GRACE_MS = 60000;

  function settings() {
    var el = document.getElementById("al-idle-settings");
    if (!el || !el.dataset.exit) { return null; }
    return { minutes: parseFloat(el.dataset.minutes || "20"), exit: el.dataset.exit };
  }

  function hideWarning() {
    var box = document.getElementById("al-idle-warning");
    if (box) { box.remove(); }
    window.alIdleWarningAt = null;
    window.alIdleLastActivity = Date.now();
  }

  function showWarning() {
    var box = document.createElement("div");
    box.id = "al-idle-warning";
    box.setAttribute("role", "alertdialog");
    box.setAttribute("aria-live", "assertive");
    box.setAttribute("aria-labelledby", "al-idle-warning-text");
    box.style.cssText = "position:fixed;left:50%;top:20%;transform:translateX(-50%);z-index:2000;" +
      "max-width:28rem;background:#fff;border:2px solid #333;border-radius:.5rem;padding:1.25rem;" +
      "box-shadow:0 .5rem 1.5rem rgba(0,0,0,.3)";
    box.innerHTML = '<p id="al-idle-warning-text"><strong>Are you still there?</strong> ' +
      "To protect your answers on a shared device, this session will end in one minute " +
      "and your answers will be erased.</p>" +
      '<button type="button" class="btn btn-primary" id="al-idle-stay">I\'m still here</button>';
    document.body.appendChild(box);
    document.getElementById("al-idle-stay").addEventListener("click", hideWarning);
    document.getElementById("al-idle-stay").focus();
    window.alIdleWarningAt = Date.now();
  }

  function activity() {
    if (window.alIdleWarningAt === null) { window.alIdleLastActivity = Date.now(); }
  }
  ["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(function (name) {
    document.addEventListener(name, activity, { passive: true });
  });

  setInterval(function () {
    var s = settings();
    if (!s) { return; }
    if (window.alIdleWarningAt === null) {
      if (Date.now() - window.alIdleLastActivity > s.minutes * 60000) { showWarning(); }
    } else if (Date.now() - window.alIdleWarningAt > GRACE_MS) {
      window.location.replace(s.exit);
    }
  }, 1000);
})();
