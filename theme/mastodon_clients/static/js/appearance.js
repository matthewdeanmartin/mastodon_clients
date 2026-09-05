(function () {
  "use strict";
  var root = document.documentElement;
  var themes = ["editorial", "garden", "studio"];
  var modes = ["system", "light", "dark"];
  try {
    var saved = JSON.parse(localStorage.getItem("client-guide-appearance") || "{}");
    if (themes.includes(saved.theme)) root.dataset.theme = saved.theme;
    if (modes.includes(saved.mode)) root.dataset.mode = saved.mode;
  } catch (_) { /* System appearance also works when storage is unavailable. */ }
  document.addEventListener("DOMContentLoaded", function () {
    var panel = document.getElementById("appearance");
    var theme = document.getElementById("theme-choice");
    var mode = document.getElementById("mode-choice");
    if (!panel || !theme || !mode) return;
    panel.hidden = false;
    theme.value = root.dataset.theme;
    mode.value = root.dataset.mode;
    function update() {
      root.dataset.theme = theme.value;
      root.dataset.mode = mode.value;
      try { localStorage.setItem("client-guide-appearance", JSON.stringify({theme: theme.value, mode: mode.value})); } catch (_) {}
    }
    theme.addEventListener("change", update);
    mode.addEventListener("change", update);
  });
})();
