// Small site-wide JS helpers: mobile nav toggle and flash auto-dismiss

document.addEventListener('DOMContentLoaded', function () {
  // Mobile nav toggle
  var toggle = document.querySelector('.navbar-toggle');
  var menu = document.getElementById('navbar-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', (!expanded).toString());
      menu.classList.toggle('open');
    });
  }

  // Auto-dismiss flash messages after 5s with fade
  var alerts = document.querySelectorAll('.flash-messages .alert');
  if (alerts.length) {
    setTimeout(function () {
      alerts.forEach(function (el) {
        el.classList.add('fading');
        // remove after transition
        setTimeout(function () { if (el && el.parentNode) el.parentNode.removeChild(el); }, 400);
      });
    }, 5000);
  }
});