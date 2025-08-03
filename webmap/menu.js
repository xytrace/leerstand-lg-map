document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("menu-toggle");
  const overlay = document.getElementById("menu-overlay");
  const backdrop = document.getElementById("menu-backdrop");

  if (!toggle || !overlay || !backdrop) return;

  // Ensure hidden state on load
  overlay.classList.remove("open");
  backdrop.classList.remove("visible");

  function openMenu() {
    overlay.classList.add("open");
    backdrop.classList.add("visible");
  }

  function closeMenu() {
    overlay.classList.remove("open");
    backdrop.classList.remove("visible");
  }

  toggle.addEventListener("click", () => {
    const isOpen = overlay.classList.contains("open");
    if (isOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  backdrop.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
});
