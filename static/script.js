/**
 * script.js - Minimal vanilla JavaScript for CampusFix.
 * Kept intentionally lightweight to preserve Python/Flask application primacy.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile navigation menu toggle
  const toggleBtn = document.getElementById('menu-toggle-btn');
  const navLinks = document.getElementById('nav-links-menu');

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', function () {
      navLinks.classList.toggle('nav-open');
    });
  }

  // 2. Auto-hide flash alerts after 6 seconds
  const alerts = document.querySelectorAll('.alert');
  if (alerts.length > 0) {
    setTimeout(function () {
      alerts.forEach(function (alert) {
        alert.style.transition = 'opacity 0.5s ease';
        alert.style.opacity = '0';
        setTimeout(function () {
          alert.remove();
        }, 500);
      });
    }, 6000);
  }
});
