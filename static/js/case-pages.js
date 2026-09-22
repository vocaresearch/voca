(function () {
  'use strict';
  function loadCase(choice) {
    var holder = choice.querySelector('[data-case-src]');
    if (!holder || holder.dataset.loaded === 'true' || holder.dataset.loading === 'true') return;
    holder.dataset.loading = 'true';
    holder.setAttribute('aria-busy', 'true');
    var status = holder.querySelector('.case-load-status');
    if (!status) { status = document.createElement('p'); status.className = 'case-load-status'; holder.appendChild(status); }
    status.textContent = 'Loading example…';
    fetch(holder.dataset.caseSrc).then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.text();
    }).then(function (text) {
      var doc = new DOMParser().parseFromString(text, 'text/html');
      var body = doc.getElementById('case-content');
      if (!body) throw new Error('Missing case content');
      holder.replaceChildren.apply(holder, Array.from(body.childNodes).map(function (node) { return document.importNode(node, true); }));
      holder.dataset.loaded = 'true';
      holder.removeAttribute('aria-live');
      // Historical/response clips are created only after the card is opened.
      if (!choice.open || choice.closest('[hidden]')) holder.querySelectorAll('audio').forEach(function (clip) { clip.pause(); });
    }).catch(function () {
      status.textContent = 'Could not load the example. Use the link above or retry.';
      var retry = holder.querySelector('.case-retry');
      if (!retry) {
        retry = document.createElement('button'); retry.type = 'button'; retry.className = 'gallery-action case-retry'; retry.textContent = 'Retry';
        retry.addEventListener('click', function () { loadCase(choice); }); holder.appendChild(retry);
      }
    }).finally(function () { holder.dataset.loading = 'false'; holder.removeAttribute('aria-busy'); });
  }
  document.querySelectorAll('.example-choice, .agent-case-choice').forEach(function (choice) {
    choice.addEventListener('toggle', function () { if (choice.open) loadCase(choice); });
    if (choice.open) loadCase(choice);
  });
})();
