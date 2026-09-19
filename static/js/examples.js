(function () {
  'use strict';
  var gallery = document.getElementById('examples');
  if (!gallery) return;
  var nav = gallery.querySelector('.example-tabs');
  var tabs = Array.from(nav.querySelectorAll('a'));
  var groups = tabs.map(function (tab) { return document.getElementById(tab.hash.slice(1)); });
  var abilities = groups.map(function (group) {
    var nav = group.querySelector('.subgroup-nav');
    var tabs = Array.from(nav.querySelectorAll('a'));
    return { group: group, nav: nav, tabs: tabs, panels: tabs.map(function (tab) {
      return document.getElementById(tab.hash.slice(1));
    }), selected: 0 };
  });

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

  function updateHash(target) {
    if (window.location.hash !== '#' + target.id) window.history.pushState(null, '', '#' + target.id);
  }

  // Both levels are ordinary links without JS, and keyboard-accessible tabs with JS.
  function wireTabs(nav, tabs, panels, select) {
    nav.setAttribute('role', 'tablist');
    tabs.forEach(function (tab, index) {
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', panels[index].id);
      panels[index].setAttribute('role', 'tabpanel');
      panels[index].setAttribute('aria-labelledby', tab.id);
      panels[index].tabIndex = 0;
      tab.addEventListener('click', function (event) {
        event.preventDefault();
        select(index);
        updateHash(panels[index]);
      });
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
  }

  function displayPanel(tabs, panels, index) {
    panels.forEach(function (panel, i) {
      var selected = i === index;
      if (!selected) pauseWithin(panel);
      panel.hidden = !selected;
      tabs[i].setAttribute('aria-selected', String(selected));
      tabs[i].tabIndex = selected ? 0 : -1;
    });
  }

  function activateAbility(state, index) {
    state.selected = index;
    displayPanel(state.tabs, state.panels, index);
    var panel = state.panels[index];
    var title = panel.querySelector('.subgroup-head h4').textContent;
    var count = panel.querySelectorAll('.example-choice').length;
    var tools = state.group.querySelector('.gallery-tools');
    tools.querySelector('.gallery-context').textContent = title + ' · ' + count + (count === 1 ? ' example' : ' examples');
    tools.querySelector('.gallery-status').textContent = '';
  }

  function activateGroup(index) {
    displayPanel(tabs, groups, index);
    activateAbility(abilities[index], abilities[index].selected);
  }

  abilities.forEach(function (state) {
    wireTabs(state.nav, state.tabs, state.panels, function (index) { activateAbility(state, index); });
    activateAbility(state, 0);
    var tools = state.group.querySelector('.gallery-tools');
    tools.hidden = false;
    var status = tools.querySelector('.gallery-status');
    tools.querySelector('[data-action="expand"]').addEventListener('click', function () {
      var panel = state.panels[state.selected];
      panel.dataset.expanded = 'true';
      panel.querySelectorAll('.example-choice').forEach(function (choice) { choice.open = true; });
      status.textContent = 'All examples in this capability are open.';
    });
    tools.querySelector('[data-action="collapse"]').addEventListener('click', function () {
      var panel = state.panels[state.selected];
      panel.querySelectorAll('.example-choice').forEach(function (choice) { choice.open = false; });
      pauseWithin(panel);
      panel.dataset.expanded = 'false';
      status.textContent = 'All examples in this capability are closed.';
    });
    tools.querySelector('[data-action="copy"]').addEventListener('click', function () {
      copyLink(state.panels[state.selected], status);
    });
  });
  wireTabs(nav, tabs, groups, activateGroup);

  gallery.querySelectorAll('.example-choice').forEach(function (choice) {
    choice.removeAttribute('name');
    var panel = choice.closest('.example-subgroup');
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
      if (!choice.open) { pauseWithin(choice); return; }
      if (panel.dataset.expanded !== 'true') panel.querySelectorAll('.example-choice').forEach(function (other) {
        if (other !== choice) { other.open = false; pauseWithin(other); }
      });
      requestAnimationFrame(function () {
        if (!choice.open || panel.hidden || panel.closest('.example-group').hidden || panel.dataset.expanded === 'true') return;
        var top = choice.getBoundingClientRect().top;
        var nav = document.getElementById('topnav');
        if (top < nav.offsetHeight || top > window.innerHeight - 80) choice.scrollIntoView({ block: 'start', behavior: 'instant' });
      });
    });
  });

  function revealHash() {
    var target = document.getElementById(window.location.hash.slice(1));
    if (!target) return;
    var group = target.closest('.example-group');
    if (!group) return;
    var index = groups.indexOf(group);
    activateGroup(index);
    var panel = target.closest('.example-subgroup');
    if (panel) activateAbility(abilities[index], abilities[index].panels.indexOf(panel));
    var choice = target.closest('.example-choice');
    if (choice) choice.open = true;
    // A capability link keeps its selector in view; a case link opens that case.
    var destination = target === panel ? abilities[index].nav : target;
    requestAnimationFrame(function () {
      if (!group.hidden && (!panel || !panel.hidden)) destination.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
  }
  activateGroup(0);
  revealHash();
  window.addEventListener('hashchange', revealHash);
  window.addEventListener('popstate', revealHash);
})();
