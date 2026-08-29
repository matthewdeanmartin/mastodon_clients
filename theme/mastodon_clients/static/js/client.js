/* Progressive enhancement for the review page: Review / Feature data tabs.
 *
 * The two panels are ordinary stacked sections in the HTML. Everything in both
 * is present, crawlable, and readable with JavaScript off (invariants 6 and 7);
 * this file only collapses them into tabs, and reveals the tablist that ships
 * hidden so a reader without JavaScript is never shown controls that cannot
 * work.
 *
 * The feature matrix is 32 rows. In the middle of a review it read as a data
 * dump; behind a tab it is available to anyone who wants it and out of the way
 * of anyone who does not.
 */

(function () {
  "use strict";

  var container = document.querySelector("[data-tabs]");
  if (!container) return;

  var shell = container.querySelector(".tablist-shell");
  var tabs = Array.prototype.slice.call(container.querySelectorAll('[role="tab"]'));
  var panels = Array.prototype.slice.call(container.querySelectorAll('[role="tabpanel"]'));
  if (!shell || tabs.length !== panels.length || !tabs.length) return;

  shell.hidden = false;
  container.classList.add("tabs-enhanced");

  function panelFor(tab) {
    return document.getElementById(tab.getAttribute("aria-controls"));
  }

  function select(tab, focus) {
    tabs.forEach(function (candidate) {
      var selected = candidate === tab;
      candidate.setAttribute("aria-selected", selected ? "true" : "false");
      // Roving tabindex: only the active tab is in the tab order, so Tab moves
      // past the tablist rather than through every tab in it.
      candidate.tabIndex = selected ? 0 : -1;
      var panel = panelFor(candidate);
      if (panel) panel.hidden = !selected;
    });
    if (focus) tab.focus();
  }

  tabs.forEach(function (tab, index) {
    tab.addEventListener("click", function () {
      select(tab, false);
      // Record the panel in the fragment so the tab survives a reload and can be
      // linked to directly.
      var panel = panelFor(tab);
      if (panel) {
        window.history.replaceState(null, "", window.location.pathname + "#" + panel.id);
      }
    });

    tab.addEventListener("keydown", function (event) {
      var next = null;
      if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
      else if (event.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
      else if (event.key === "Home") next = tabs[0];
      else if (event.key === "End") next = tabs[tabs.length - 1];
      if (next) {
        event.preventDefault();
        select(next, true);
      }
    });
  });

  /* Open the tab a link asked for.
   *
   * Both the panel id (#panel-features) and any heading inside a panel work, so
   * an existing link to #features or #observations still lands somewhere useful
   * rather than on a hidden element.
   */
  function selectFromHash() {
    var id = window.location.hash.replace(/^#/, "");
    if (!id) return false;

    var target = document.getElementById(id);
    if (!target) return false;

    for (var i = 0; i < panels.length; i++) {
      if (panels[i] === target || panels[i].contains(target)) {
        select(tabs[i], false);
        if (panels[i] !== target) target.scrollIntoView();
        return true;
      }
    }
    return false;
  }

  if (!selectFromHash()) select(tabs[0], false);
  window.addEventListener("hashchange", selectFromHash);
})();
