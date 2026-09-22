(function () {
  'use strict';
  var cache = new Map();
  var pending = new Map();
  var queue = [];
  var active = 0;
  var choices = Array.from(document.querySelectorAll('.example-choice, .agent-case-choice'));
  var saveData = navigator.connection && navigator.connection.saveData;

  function source(choice) {
    var holder = choice.querySelector('[data-case-src]');
    return holder && holder.dataset.caseSrc;
  }
  function fetchCase(url) {
    if (cache.has(url)) return Promise.resolve(cache.get(url));
    if (pending.has(url)) return pending.get(url);
    var request = fetch(url).then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.text();
    }).then(function (text) {
      var body = new DOMParser().parseFromString(text, 'text/html').getElementById('case-content');
      if (!body) throw new Error('Missing case content');
      cache.set(url, body);
      return body;
    }).finally(function () { pending.delete(url); });
    pending.set(url, request);
    return request;
  }
  function mount(choice, holder, body) {
    holder.replaceChildren.apply(holder, Array.from(body.childNodes).map(function (node) {
      return document.importNode(node, true);
    }));
    holder.dataset.loaded = 'true';
    holder.removeAttribute('aria-live');
    if (!choice.open || choice.closest('[hidden]')) holder.querySelectorAll('audio').forEach(function (clip) { clip.pause(); });
    document.dispatchEvent(new CustomEvent('case:loaded', { detail: choice }));
  }
  function loadCase(choice) {
    var holder = choice.querySelector('[data-case-src]');
    if (!holder || holder.dataset.loaded === 'true' || holder.dataset.loading === 'true') return;
    var url = source(choice);
    if (cache.has(url)) { mount(choice, holder, cache.get(url)); return; }
    holder.dataset.loading = 'true';
    holder.setAttribute('aria-busy', 'true');
    var status = holder.querySelector('.case-load-status');
    if (!status) { status = document.createElement('p'); status.className = 'case-load-status'; holder.appendChild(status); }
    status.textContent = 'Loading example…';
    fetchCase(url).then(function (body) { mount(choice, holder, body); }).catch(function () {
      status.textContent = 'Could not load the example. Use the link above or retry.';
      if (!holder.querySelector('.case-retry')) {
        var retry = document.createElement('button');
        retry.type = 'button'; retry.className = 'gallery-action case-retry'; retry.textContent = 'Retry';
        retry.addEventListener('click', function () { loadCase(choice); }); holder.appendChild(retry);
      }
    }).finally(function () { holder.dataset.loading = 'false'; holder.removeAttribute('aria-busy'); });
  }
  function pump() {
    while (active < 2 && queue.length) {
      var choice = queue.shift();
      if (choice.closest('[hidden]') || cache.has(source(choice))) continue;
      active++;
      fetchCase(source(choice)).catch(function () {}).finally(function () { active--; pump(); });
    }
  }
  function prefetchPanel(panel) {
    if (saveData || panel.closest('[hidden]')) return;
    panel.querySelectorAll('.example-choice, .agent-case-choice').forEach(function (choice) {
      if (!choice.hidden && !cache.has(source(choice)) && queue.indexOf(choice) < 0) queue.push(choice);
    });
    pump();
  }
  window.VocaCases = { load: loadCase, prefetch: prefetchPanel };
  choices.forEach(function (choice) {
    choice.addEventListener('toggle', function () { if (choice.open) loadCase(choice); });
    var summary = choice.querySelector('summary');
    function anticipate() { if (!saveData) fetchCase(source(choice)).catch(function () {}); }
    summary.addEventListener('pointerenter', anticipate);
    summary.addEventListener('focus', anticipate);
    // Populate from the memory cache in the click event, before the next paint.
    summary.addEventListener('click', function () { if (!choice.open) loadCase(choice); });
    if (choice.open) loadCase(choice);
  });
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { if (entry.isIntersecting) prefetchPanel(entry.target); });
    }, { rootMargin: '500px' });
    document.querySelectorAll('.example-subgroup, .agent-subgroup').forEach(function (panel) { observer.observe(panel); });
  }
})();
