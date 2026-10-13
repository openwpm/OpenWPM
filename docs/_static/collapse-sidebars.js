// Furo loads scripts at the end of <body>, so on a slow parse the saved state may land after first paint.
(function () {
  var KEY = "openwpm-docs-collapsed";
  var PANELS = {
    nav: {label: "Toggle navigation", icon: '<rect x="3" y="4" width="18" height="16" rx="2"/><line x1="9" y1="4" x2="9" y2="20"/>'},
    toc: {label: "Toggle outline", icon: '<rect x="3" y="4" width="18" height="16" rx="2"/><line x1="15" y1="4" x2="15" y2="20"/>'},
  };
  var root = document.documentElement;

  // Storage throws when blocked (private modes, cookie policies); the buttons still work without it.
  function load() {
    try { return (localStorage.getItem(KEY) || "").split(","); } catch (e) { return []; }
  }
  function save() {
    var hidden = Object.keys(PANELS).filter(function (p) { return root.classList.contains("collapse-" + p); });
    try { localStorage.setItem(KEY, hidden.join(",")); } catch (e) {}
  }

  load().forEach(function (p) { if (PANELS[p]) root.classList.add("collapse-" + p); });

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.querySelector(".content-icon-container");
    if (!container) return;
    var anchor = container.querySelector(".theme-toggle-container");
    Object.keys(PANELS).forEach(function (p) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "collapse-toggle collapse-toggle-" + p;
      b.setAttribute("aria-label", PANELS[p].label);
      b.title = PANELS[p].label;
      b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + PANELS[p].icon + "</svg>";
      // aria-pressed is true while the sidebar is shown.
      function sync() { b.setAttribute("aria-pressed", String(!root.classList.contains("collapse-" + p))); }
      b.addEventListener("click", function () {
        root.classList.toggle("collapse-" + p);
        sync();
        save();
      });
      sync();
      container.insertBefore(b, anchor);
    });
  });
})();
