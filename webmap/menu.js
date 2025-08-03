// menu.js
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("menu-toggle");
  const overlay = document.getElementById("menu-overlay");

  if (!toggle || !overlay) return;

  // Stelle sicher, dass das Menü beim Laden versteckt ist
  overlay.classList.add("menu-hidden");
  overlay.style.display = "none";

  toggle.addEventListener("click", () => {
    const isHidden = overlay.classList.contains("menu-hidden");

    if (isHidden) {
      // Menü anzeigen
      overlay.style.display = "block";
      // Erzwinge ein Reflow, damit transition korrekt läuft
      void overlay.offsetWidth;
      overlay.classList.remove("menu-hidden");
    } else {
      // Menü verstecken
      overlay.classList.add("menu-hidden");
      setTimeout(() => {
        if (overlay.classList.contains("menu-hidden")) {
          overlay.style.display = "none";
        }
      }, 300); // Dauer der CSS-Transition in ms
    }
  });
});
