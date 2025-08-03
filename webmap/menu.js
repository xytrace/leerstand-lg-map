document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("menu-toggle");
  const overlay = document.getElementById("menu-overlay");
  const backdrop = document.getElementById("menu-backdrop");

  if (!toggle || !overlay || !backdrop) return;

  // Set initial state
  overlay.classList.remove("open");
  backdrop.classList.remove("visible");
  toggle.textContent = "☰"; // Hamburger on load

  function openMenu() {
    overlay.classList.add("open");
    backdrop.classList.add("visible");
    toggle.textContent = "✕"; // Change to X when open
  }

  function closeMenu() {
    overlay.classList.remove("open");
    backdrop.classList.remove("visible");
    toggle.textContent = "☰"; // Back to hamburger when closed
  }

  toggle.addEventListener("click", () => {
    const isOpen = overlay.classList.contains("open");
    isOpen ? closeMenu() : openMenu();
  });

  backdrop.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
});
