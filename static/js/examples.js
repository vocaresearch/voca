(function () {
  'use strict';
  var gallery = document.getElementById('examples');
  if (!gallery) return;
  var tablist = gallery.querySelector('.example-tabs');
  var tabs = Array.from(tablist.querySelectorAll('a'));
  var groups = tabs.map(function (tab) { return document.getElementById(tab.hash.slice(1)); });

  function pauseWithin(element) {
    element.querySelectorAll('audio').forEach(function (clip) { clip.pause(); });
  }

  function copyLink(target, status) {
    var url = window.location.href.split('#')[0] + '#' + target.id;
    function fallback() { status.textContent = 'Copy this link: ' + url; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () { status.textContent = 'Link copied.'; }, fallback);
    } else fallback();
  }

  // Without JavaScript, all groups and native expandable examples remain usable.
  tablist.setAttribute('role', 'tablist');
  tabs.forEach(function (tab, index) {
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', groups[index].id);
    groups[index].setAttribute('role', 'tabpanel');
    groups[index].setAttribute('aria-labelledby', tab.id);
    tab.addEventListener('click', function () { activate(index); });
    tab.addEventListener('keydown', function (event) {
      var next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      tabs[next].focus();
      tabs[next].click();
    });
  });

  function activate(index) {
    groups.forEach(function (group, i) {
      var selected = i === index;
      if (!selected) pauseWithin(group);
      group.hidden = !selected;
      tabs[i].setAttribute('aria-selected', String(selected));
      tabs[i].tabIndex = selected ? 0 : -1;
    });
  }

  gallery.querySelectorAll('.example-choice').forEach(function (choice) {
    // Preserve native name-based exclusivity for the no-JS fallback, while allowing
    // the explicit bulk controls to open several cases when JavaScript is active.
    choice.removeAttribute('name');
    var actions = document.createElement('div');
    actions.className = 'case-actions';
    var copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'gallery-action';
    copy.textContent = 'Copy example link';
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'gallery-action';
    close.textContent = 'Close example';
    var status = document.createElement('span');
    status.className = 'gallery-status';
    status.setAttribute('role', 'status');
    copy.addEventListener('click', function () { copyLink(choice, status); });
    close.addEventListener('click', function () {
      choice.open = false;
      pauseWithin(choice);
      choice.querySelector('summary').focus();
      choice.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
    actions.append(copy, close, status);
    choice.querySelector('article').appendChild(actions);
    choice.addEventListener('toggle', function () {
      if (!choice.open) {
        pauseWithin(choice);
        return;
      }
      // Also enforce exclusivity in browsers without support for details[name].
      var group = choice.closest('.example-group');
      if (group.dataset.expanded !== 'true') group.querySelectorAll('.example-choice').forEach(function (other) {
        if (other !== choice) { other.open = false; pauseWithin(other); }
      });
      // Opening a lower example closes content above it; keep its selector in view.
      requestAnimationFrame(function () {
        if (!choice.open || group.hidden || group.dataset.expanded === 'true') return;
        var top = choice.getBoundingClientRect().top;
        var nav = document.getElementById('topnav');
        if (top < nav.offsetHeight || top > window.innerHeight - 80) {
          choice.scrollIntoView({ block: 'start', behavior: 'instant' });
        }
      });
    });
  });

  gallery.querySelectorAll('.gallery-tools').forEach(function (tools) {
    tools.hidden = false;
    var group = tools.closest('.example-group');
    var status = tools.querySelector('.gallery-status');
    var search = tools.querySelector('input[type="search"]');
    function setStatus(message) { status.textContent = message; }
    tools.querySelector('[data-action="expand"]').addEventListener('click', function () {
      group.dataset.expanded = 'true';
      group.querySelectorAll('.example-choice:not(.is-filtered)').forEach(function (choice) { choice.open = true; });
      setStatus('All matching examples are open.');
    });
    tools.querySelector('[data-action="collapse"]').addEventListener('click', function () {
      group.querySelectorAll('.example-choice').forEach(function (choice) { choice.open = false; pauseWithin(choice); });
      group.dataset.expanded = 'false';
      setStatus('All examples in this category are closed.');
    });
    tools.querySelector('[data-action="copy"]').addEventListener('click', function () {
      copyLink(group, status);
    });
    search.addEventListener('input', function () {
      var query = search.value.trim().toLowerCase();
      var shown = 0;
      group.querySelectorAll('.example-subgroup').forEach(function (subgroup) {
        var matches = 0;
        subgroup.querySelectorAll('.example-choice').forEach(function (choice) {
          var match = !query || choice.textContent.toLowerCase().indexOf(query) !== -1;
          choice.classList.toggle('is-filtered', !match);
          if (!match) pauseWithin(choice);
          if (match) { matches += 1; shown += 1; }
        });
        subgroup.classList.toggle('is-empty', matches === 0);
      });
      setStatus(query ? (shown + ' matching example' + (shown === 1 ? '' : 's') + '.') : '');
    });
    group.querySelectorAll('.subgroup-nav a').forEach(function (link) {
      link.addEventListener('click', function () {
        search.value = '';
        search.dispatchEvent(new Event('input'));
      });
    });
  });

  function revealHash() {
    var target = document.getElementById(window.location.hash.slice(1));
    if (!target) return false;
    var group = target.closest('.example-group');
    if (!group) return false;
    activate(groups.indexOf(group));
    var search = group.querySelector('input[type="search"]');
    if (search.value && target !== group) {
      search.value = '';
      search.dispatchEvent(new Event('input'));
    }
    var choice = target.closest('.example-choice');
    if (choice) choice.open = true;
    requestAnimationFrame(function () { target.scrollIntoView({ block: 'start', behavior: 'instant' }); });
    return true;
  }
  activate(0);
  revealHash();
  window.addEventListener('hashchange', revealHash);
})();
