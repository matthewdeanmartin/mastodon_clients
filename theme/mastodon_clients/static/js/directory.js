/* Progressive enhancement for the client directory (spec 28, 29).
 *
 * Two rules govern this file.
 *
 * It never fetches the dataset. Every row it filters and sorts is already in the
 * DOM, server-rendered (invariant 6). Delete this script and the page keeps
 * working: the table is complete, every client is linked, and only the controls
 * disappear -- which is why the form ships `hidden` and is revealed here.
 *
 * It writes filter state to the URL *fragment*, never the query string, so no
 * arbitrary filter combination becomes a crawlable URL (spec 30). Curated
 * facets get real static pages instead.
 */

(function () {
  "use strict";

  var form = document.getElementById("directory-controls");
  var table = document.getElementById("directory-table");
  if (!form || !table) return;

  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var cards = Array.prototype.slice.call(document.querySelectorAll("#directory-cards .client-card"));
  var cardsContainer = document.getElementById("directory-cards");
  var tableView = document.getElementById("table-view");
  var viewControls = document.getElementById("view-controls");
  if (viewControls && tableView && cardsContainer) {
    viewControls.hidden = false;
    tableView.hidden = true;
    viewControls.querySelectorAll("button").forEach(function (button) {
      button.addEventListener("click", function () {
        var showCards = button.dataset.view === "cards";
        cardsContainer.hidden = !showCards;
        tableView.hidden = showCards;
        tableView.open = !showCards;
        viewControls.querySelectorAll("button").forEach(function (item) {
          item.setAttribute("aria-pressed", String(item === button));
        });
      });
    });
  }
  var count = document.getElementById("filter-count");
  var reset = document.getElementById("filter-reset");

  // The markup ships hidden so a visitor without JavaScript is never shown
  // controls that cannot do anything.
  form.hidden = false;

  /* --- filtering -------------------------------------------------------- */

  function readState() {
    var features = [];
    form.querySelectorAll('input[name="feature"]:checked').forEach(function (box) {
      features.push(box.value);
    });
    return {
      q: (form.elements.q.value || "").trim().toLowerCase(),
      audience: form.elements.audience.value,
      source: form.elements.source.value,
      deployment: form.elements.deployment.value,
      status: form.elements.status.value,
      standalone: form.elements.standalone.checked,
      features: features
    };
  }

  function matches(row, state) {
    var data = row.dataset;

    if (state.q && data.search.indexOf(state.q) === -1) return false;
    if (state.audience && data.audiences.split(" ").indexOf(state.audience) === -1) return false;
    if (state.source && data.source !== state.source) return false;
    if (state.deployment === "self-hostable") {
      if (!["self-hostable", "hosted-and-self-hostable"].includes(data.deployment)) return false;
    } else if (state.deployment && data.deployment !== state.deployment) return false;
    if (state.status && data.status !== state.status) return false;
    if (state.standalone && data.standalone !== "yes") return false;

    // A required feature means the client offers it (yes or partial); the
    // data-features attribute already holds only those.
    var have = data.features.split(" ");
    for (var i = 0; i < state.features.length; i++) {
      if (have.indexOf(state.features[i]) === -1) return false;
    }
    return true;
  }

  function apply() {
    var state = readState();
    var shown = 0;

    rows.forEach(function (row) {
      var visible = matches(row, state);
      row.hidden = !visible;
      if (visible) shown++;
    });

    cards.forEach(function (card) {
      var row = rows.find(function (item) { return item.dataset.name === card.dataset.name; });
      card.hidden = row ? row.hidden : false;
    });
    var empty = document.getElementById("no-results");
    if (empty) empty.hidden = shown !== 0;
    var active = document.getElementById("active-filters");
    if (active) {
      active.replaceChildren();
      Array.prototype.forEach.call(form.elements, function (input) {
        if (!input.name || !input.value || input.type === "fieldset" || input.type === "search") return;
        if (input.type === "checkbox" && !input.checked) return;
        if (input.type !== "checkbox" && input.tagName !== "SELECT") return;
        var chip = document.createElement("button");
        chip.type = "button";
        var label = input.tagName === "SELECT" ? input.options[input.selectedIndex].text : input.labels[0].textContent;
        chip.textContent = label + " ×";
        chip.setAttribute("aria-label", "Remove filter: " + label);
        chip.addEventListener("click", function () {
          if (input.type === "checkbox") input.checked = false; else input.value = "";
          apply();
        });
        active.appendChild(chip);
      });
    }
    if (count) {
      count.textContent =
        shown === rows.length
          ? "Showing all " + rows.length + " clients"
          : "Showing " + shown + " of " + rows.length + " clients";
    }
    writeFragment(state);
  }

  /* --- sorting ---------------------------------------------------------- */

  /* The server renders rows best-rated first, so the script starts in that same
   * state. Leaving it null meant the first click on "Rating" sorted ascending --
   * worst first -- because the script did not know the order it had inherited.
   */
  var sortState = { key: "rating", direction: -1 };

  function sortValue(row, key) {
    var data = row.dataset;
    switch (key) {
      case "rating":
        return parseFloat(data.rating) || 0;
      case "reviewed":
        return data.reviewed;
      case "status":
        // Rank by how well-maintained, so a status sort reads as an ordering
        // rather than as alphabetical noise.
        return [
          "actively-maintained",
          "maintained",
          "low-activity",
          "unknown",
          "possibly-unmaintained",
          "unmaintained",
          "discontinued"
        ].indexOf(data.status);
      case "source":
        return data.source;
      case "deployment":
        return data.deployment;
      default:
        return data.name;
    }
  }

  function sortBy(key) {
    // Clicking the active column reverses it; a new column starts ascending,
    // except rating and date, where "best first" is the useful default.
    if (sortState.key === key) {
      sortState.direction = -sortState.direction;
    } else {
      sortState.key = key;
      sortState.direction = key === "rating" || key === "reviewed" ? -1 : 1;
    }

    var sorted = rows.slice().sort(function (a, b) {
      var left = sortValue(a, sortState.key);
      var right = sortValue(b, sortState.key);
      if (left < right) return -1 * sortState.direction;
      if (left > right) return 1 * sortState.direction;
      // Name is the stable tiebreak, so equal rows never shuffle between sorts.
      return a.dataset.name < b.dataset.name ? -1 : 1;
    });

    sorted.forEach(function (row) {
      tbody.appendChild(row);
    });

    table.querySelectorAll("th[data-sort]").forEach(function (th) {
      if (th.dataset.sort === sortState.key) {
        th.setAttribute("aria-sort", sortState.direction === 1 ? "ascending" : "descending");
      } else {
        th.setAttribute("aria-sort", "none");
      }
    });
  }

  table.querySelectorAll("th[data-sort]").forEach(function (th) {
    th.setAttribute("aria-sort", "none");

    // The header becomes a real button so it is reachable and operable by
    // keyboard and announced correctly, rather than a click handler on a th.
    var label = th.textContent.trim();
    var button = document.createElement("button");
    button.type = "button";
    button.className = "sort-button";
    button.textContent = label;
    button.setAttribute("aria-label", "Sort by " + label);
    th.textContent = "";
    th.appendChild(button);

    button.addEventListener("click", function () {
      sortBy(th.dataset.sort);
    });
  });

  /* --- fragment state --------------------------------------------------- */

  // Deliberately the fragment and not the query string: this is interface
  // state, not a page (spec 30).
  function writeFragment(state) {
    var parts = [];
    if (state.q) parts.push("q=" + encodeURIComponent(state.q));
    if (state.audience) parts.push("audience=" + state.audience);
    if (state.source) parts.push("source=" + state.source);
    if (state.deployment) parts.push("deployment=" + state.deployment);
    if (state.status) parts.push("status=" + state.status);
    if (state.standalone) parts.push("standalone=1");
    if (state.features.length) parts.push("features=" + state.features.join(","));

    var fragment = parts.join("&");
    var url = window.location.pathname + window.location.search + (fragment ? "#" + fragment : "");
    window.history.replaceState(null, "", url);
  }

  function readFragment() {
    var fragment = window.location.hash.replace(/^#/, "");
    if (!fragment) return;

    fragment.split("&").forEach(function (pair) {
      var bits = pair.split("=");
      var key = bits[0];
      var value;
      try { value = decodeURIComponent(bits.slice(1).join("=") || ""); } catch (_) { return; }

      if (key === "q") form.elements.q.value = value;
      else if (key === "standalone") form.elements.standalone.checked = true;
      else if (key === "features") {
        value.split(",").forEach(function (id) {
          var box = document.getElementById("filter-feature-" + id);
          if (box) box.checked = true;
        });
      } else if (form.elements[key]) {
        // Older shared filters used a separate value for publicly hosted clients
        // that also publish a self-hostable build.
        form.elements[key].value = key === "deployment" && value === "hosted-and-self-hostable" ? "self-hostable" : value;
      }
    });
  }

  /* --- wiring ----------------------------------------------------------- */

  form.addEventListener("input", apply);
  form.addEventListener("change", apply);
  form.addEventListener("submit", function (event) {
    // There is nothing to submit; filtering is live.
    event.preventDefault();
  });

  if (reset) {
    reset.addEventListener("click", function () {
      form.reset();
      apply();
    });
  }

  // Reflect the server-rendered order in the header, without re-sorting: the
  // rows already arrive in this order, and re-sorting would only risk disagreeing
  // with the HTML a non-JavaScript reader sees.
  table.querySelectorAll("th[data-sort]").forEach(function (th) {
    if (th.dataset.sort === sortState.key) {
      th.setAttribute("aria-sort", "descending");
    }
  });

  window.addEventListener("hashchange", function () { form.reset(); readFragment(); apply(); });
  readFragment();
  apply();
})();
