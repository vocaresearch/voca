(function () {
  'use strict';
  var gallery = document.getElementById('agent-cases');
  if (!gallery) return;
  var modelButtons = Array.from(gallery.querySelectorAll('.agent-model-filter button'));
  var selectedModel = 'all';
  var selectedOutcome = 0;

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
        var available = tabs.filter(function (item) { return !item.hidden; });
        var current = available.indexOf(tab);
        var next;
        if (event.key === 'ArrowRight') next = (current + 1) % available.length;
        else if (event.key === 'ArrowLeft') next = (current + available.length - 1) % available.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = available.length - 1;
        else return;
        event.preventDefault();
        available[next].focus();
        available[next].click();
      });
    });
  }

  function activateSubgroup(state, index) {
    if (state.tabs[index].hidden) index = state.tabs.findIndex(function (tab) { return !tab.hidden; });
    if (index < 0) return;
    state.selected = index;
    display(state.tabs, state.panels, index);
  }

  function activateOutcome(index) {
    selectedOutcome = index;
    display(outcomeTabs, outcomes, index);
    activateSubgroup(subgroupStates[index], subgroupStates[index].selected);
  }

  function visibleCount(panel) {
    return panel.querySelectorAll('.agent-case-choice:not([hidden])').length;
  }

  function filterModel(model, keepSelection) {
    selectedModel = model;
    modelButtons.forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.model === model));
    });
    gallery.querySelectorAll('.agent-case-choice').forEach(function (choice) {
      choice.hidden = model !== 'all' && choice.dataset.model !== model;
      if (choice.hidden) { choice.open = false; pauseWithin(choice); }
    });
    subgroupStates.forEach(function (state, i) {
      var count = visibleCount(state.outcome);
      outcomeTabs[i].querySelector('span').textContent = count;
      outcomeTabs[i].hidden = count === 0;
      var heading = state.outcome.querySelector('.sub-h');
      heading.textContent = heading.dataset.title + ' · ' + count + ' cases';
      state.panels.forEach(function (panel, j) {
        var n = visibleCount(panel);
        state.tabs[j].querySelector('b').textContent = n;
        state.tabs[j].hidden = n === 0;
        panel.querySelector('.subgroup-count').textContent = n + ' cases';
        panel.querySelector('.agent-empty').hidden = n !== 0;
      });
      if (!keepSelection && !visibleCount(state.panels[state.selected])) {
        var next = state.panels.findIndex(function (panel) { return visibleCount(panel) > 0; });
        if (next >= 0) state.selected = next;
      }
    });
    if (!keepSelection && !visibleCount(outcomes[selectedOutcome])) {
      var next = outcomes.findIndex(function (panel) { return visibleCount(panel) > 0; });
      if (next >= 0) selectedOutcome = next;
    }
    var total = visibleCount(gallery);
    var label = model === 'all' ? 'both models' : modelButtons.find(function (button) {
      return button.dataset.model === model;
    }).childNodes[0].textContent.trim();
    gallery.querySelector('.agent-filter-status').textContent = 'Showing ' + total + ' cases across result groups for ' + label + '.';
    activateOutcome(selectedOutcome);
  }

  modelButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      filterModel(button.dataset.model, false);
      updateHash(subgroupStates[selectedOutcome].panels[subgroupStates[selectedOutcome].selected]);
    });
  });

  subgroupStates.forEach(function (state) {
    wireTabs(state.nav, state.tabs, state.panels, function (index) { activateSubgroup(state, index); });
    activateSubgroup(state, 0);
  });
  wireTabs(outcomeNav, outcomeTabs, outcomes, activateOutcome);

  gallery.querySelectorAll('.agent-case-choice').forEach(function (choice) {
    choice.addEventListener('toggle', function () {
      if (!choice.open) { pauseWithin(choice); return; }
      var panel = choice.closest('.agent-subgroup');
      if (panel) panel.querySelectorAll('.agent-case-choice').forEach(function (other) {
        if (other !== choice) { other.open = false; pauseWithin(other); }
      });
    });
  });
  gallery.addEventListener('click', function (event) {
    var button = event.target.closest('.agent-copy-case, .agent-close-case');
    if (!button) return;
    var choice = button.closest('.agent-case-choice');
    if (button.classList.contains('agent-copy-case')) {
      copyLink(choice, choice.querySelector('.agent-case-actions .gallery-status'));
    } else {
      choice.open = false;
      pauseWithin(choice);
      choice.querySelector('summary').focus();
      choice.scrollIntoView({ block: 'start', behavior: 'instant' });
    }
  });

  function revealHash() {
    var target = document.getElementById(window.location.hash.slice(1));
    if (!target) return;
    var outcome = target.closest('.agent-outcome');
    if (!outcome) return;
    var outcomeIndex = outcomes.indexOf(outcome);
    if (outcomeIndex < 0) return;
    var choice = target.closest('.agent-case-choice');
    if (choice && selectedModel !== 'all' && choice.dataset.model !== selectedModel) {
      filterModel(choice.dataset.model, true);
    }
    activateOutcome(outcomeIndex);
    var panel = target.closest('.agent-subgroup');
    if (panel) {
      var state = subgroupStates[outcomeIndex];
      var panelIndex = state.panels.indexOf(panel);
      if (panelIndex >= 0) activateSubgroup(state, panelIndex);
    }
    if (choice) choice.open = true;
    requestAnimationFrame(function () {
      if (!outcome.hidden && (!panel || !panel.hidden)) target.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
  }

  filterModel('all', false);
  revealHash();
  window.addEventListener('hashchange', revealHash);
  window.addEventListener('popstate', revealHash);
})();
