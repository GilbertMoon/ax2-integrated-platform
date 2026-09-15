(() => {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;
  const currentPath = window.location.pathname;
  sidebar.querySelectorAll(".sidebar-category").forEach(category => {
    // Keep the current destination visible, including nested LMS pages.
    const active = category.querySelector(".sidebar-nav-link.active");
    const currentLink = Array.from(category.querySelectorAll("a[href]")).find(link => {
      const path = new URL(link.href, window.location.origin).pathname;
      return path === currentPath || (path === "/lms/" && currentPath.startsWith(path));
    });
    if (active || currentLink) category.open = true;
  });
})();
