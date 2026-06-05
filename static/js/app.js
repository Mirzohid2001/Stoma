(function () {
  'use strict';

  /* Joriy sahifani navbar da belgilash */
  var path = window.location.pathname;
  document.querySelectorAll('.navbar .nav-link[href], .navbar .dropdown-item[href]').forEach(function (link) {
    try {
      var url = new URL(link.href);
      if (url.pathname === path || (path !== '/' && url.pathname !== '/' && path.startsWith(url.pathname) && url.pathname.length > 1)) {
        link.classList.add('active');
        var dropdown = link.closest('.dropdown');
        if (dropdown) {
          var toggle = dropdown.querySelector('.dropdown-toggle');
          if (toggle) toggle.classList.add('active');
        }
      }
    } catch (e) { /* skip */ }
  });

  /* Alertlarni 5 soniyadan keyin yumshoq yopish */
  document.querySelectorAll('.alert-dismissible.auto-fade').forEach(function (el) {
    setTimeout(function () {
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        bootstrap.Alert.getOrCreateInstance(el).close();
      }
    }, 5000);
  });

  /* Mobil: jadval qatoriga bosilganda highlight */
  document.querySelectorAll('.table-hover tbody tr[data-href]').forEach(function (row) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function (e) {
      if (e.target.closest('a, button, form, input, select')) return;
      window.location = row.dataset.href;
    });
  });
})();
