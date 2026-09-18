(function () {
  "use strict";

  var root = document.getElementById("brainstorm-root");
  if (!root) return;

  window.addEventListener(
    "wheel",
    function (event) {
      if (!(event.ctrlKey || event.metaKey)) return;
      event.preventDefault();
    },
    {
      capture: true,
      passive: false
    }
  );
}());
