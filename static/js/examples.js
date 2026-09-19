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
    choice.addEventListener('toggle', function () {
      if (!choice.open) {
        pauseWithin(choice);
        return;
      }
      // Also enforce exclusivity in browsers without support for details[name].
      var group = choice.closest('.example-group');
      group.querySelectorAll('.example-choice').forEach(function (other) {
        if (other !== choice) {
          other.open = false;
          pauseWithin(other);
        }
      });
      // Opening a lower example closes content above it; keep its selector in view.
      requestAnimationFrame(function () {
        if (!choice.open || group.hidden) return;
        var top = choice.getBoundingClientRect().top;
        var nav = document.getElementById('topnav');
        if (top < nav.offsetHeight || top > window.innerHeight - 80) {
          choice.scrollIntoView({ block: 'start', behavior: 'instant' });
        }
      });
    });
  });

  function revealHash() {
    var target = document.getElementById(window.location.hash.slice(1));
    if (!target) return false;
    var group = target.closest('.example-group');
    if (!group) return false;
    activate(groups.indexOf(group));
    var choice = target.closest('.example-choice');
    if (choice) choice.open = true;
    requestAnimationFrame(function () { target.scrollIntoView({ block: 'start', behavior: 'instant' }); });
    return true;
  }
  activate(0);
  revealHash();
  window.addEventListener('hashchange', revealHash);
})();
