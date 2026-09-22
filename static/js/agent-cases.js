(function () {
  'use strict';
  var gallery = document.getElementById('agent-cases');
  if (!gallery) return;

  var outcomeNav = gallery.querySelector('.agent-outcome-tabs');
  var outcomeTabs = Array.from(outcomeNav.querySelectorAll('a'));
  var outcomes = outcomeTabs.map(function (tab) { return document.getElementById(tab.hash.slice(1)); });
  var subgroupStates = outcomes.map(function (outcome) {
    var nav = outcome.querySelector('.agent-subgroup-nav');
    var tabs = Array.from(nav.querySelectorAll('a'));
    return {
      outcome: outcome,
      nav: nav,
      tabs: tabs,
      panels: tabs.map(function (tab) { return document.getElementById(tab.hash.slice(1)); }),
      selected: 0
    };
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

  function display(tabs, panels, index) {
    panels.forEach(function (panel, i) {
      var selected = i === index;
      if (!selected) pauseWithin(panel);
      panel.hidden = !selected;
      tabs[i].setAttribute('aria-selected', String(selected));
      tabs[i].tabIndex = selected ? 0 : -1;
    });
  }

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

  function activateSubgroup(state, index) {
    state.selected = index;
    display(state.tabs, state.panels, index);
  }

  function activateOutcome(index) {
    display(outcomeTabs, outcomes, index);
    activateSubgroup(subgroupStates[index], subgroupStates[index].selected);
  }

  subgroupStates.forEach(function (state) {
    wireTabs(state.nav, state.tabs, state.panels, function (index) { activateSubgroup(state, index); });
    activateSubgroup(state, 0);
  });
  wireTabs(outcomeNav, outcomeTabs, outcomes, activateOutcome);

  function loadJson(details) {
    var loader = details.querySelector('.agent-json-loader');
    if (!loader || loader.dataset.loaded === 'true' || loader.dataset.loading === 'true') return;
    loader.dataset.loading = 'true';
    var status = loader.querySelector('.gallery-status');
    status.textContent = 'Loading recorded JSON…';
    fetch(loader.dataset.jsonUrl, { credentials: 'same-origin' }).then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    }).then(function (data) {
      var pre = document.createElement('pre');
      pre.textContent = JSON.stringify(data, null, 2);
      loader.appendChild(pre);
      loader.dataset.loaded = 'true';
      status.textContent = 'Loaded.';
    }).catch(function (error) {
      status.textContent = 'Could not load the JSON record (' + error.message + ').';
    }).finally(function () {
      loader.dataset.loading = 'false';
    });
  }

  gallery.querySelectorAll('.agent-json').forEach(function (details) {
    details.addEventListener('toggle', function () { if (details.open) loadJson(details); });
  });

  gallery.querySelectorAll('.agent-case-choice').forEach(function (choice) {
    choice.addEventListener('toggle', function () {
      if (!choice.open) { pauseWithin(choice); return; }
      var panel = choice.closest('.agent-subgroup');
      if (panel) panel.querySelectorAll('.agent-case-choice').forEach(function (other) {
        if (other !== choice) { other.open = false; pauseWithin(other); }
      });
    });
    var copy = choice.querySelector('.agent-copy-case');
    var close = choice.querySelector('.agent-close-case');
    var status = choice.querySelector('.agent-case-actions .gallery-status');
    if (copy) copy.addEventListener('click', function () { copyLink(choice, status); });
    if (close) close.addEventListener('click', function () {
      choice.open = false;
      pauseWithin(choice);
      choice.querySelector('summary').focus();
      choice.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
  });

  function revealHash() {
    var target = document.getElementById(window.location.hash.slice(1));
    if (!target) return;
    var outcome = target.closest('.agent-outcome');
    if (!outcome) return;
    var outcomeIndex = outcomes.indexOf(outcome);
    if (outcomeIndex < 0) return;
    activateOutcome(outcomeIndex);
    var panel = target.closest('.agent-subgroup');
    if (panel) {
      var state = subgroupStates[outcomeIndex];
      var panelIndex = state.panels.indexOf(panel);
      if (panelIndex >= 0) activateSubgroup(state, panelIndex);
    }
    var choice = target.closest('.agent-case-choice');
    if (choice) choice.open = true;
    requestAnimationFrame(function () {
      if (!outcome.hidden && (!panel || !panel.hidden)) target.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
  }

  activateOutcome(0);
  revealHash();
  window.addEventListener('hashchange', revealHash);
  window.addEventListener('popstate', revealHash);
})();
