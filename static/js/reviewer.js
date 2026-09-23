(function () {
  'use strict';
  var panels = Array.from(document.querySelectorAll('.example-subgroup, .agent-subgroup'));
  panels.forEach(function (panel) {
    var all = Array.from(panel.querySelectorAll('.example-choice, .agent-case-choice'));
    var bar = document.createElement('div');
    bar.className = 'review-browser';
    bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'Browse cases in this category');
    bar.innerHTML = '<span class="review-position" aria-live="polite"></span><label class="review-selector"><span class="sr-only">Choose a case</span><select aria-label="Choose a case"></select></label><div class="review-buttons"><button type="button" class="gallery-action" data-review="prev">← Previous</button><button type="button" class="gallery-action" data-review="next">Start browsing →</button><button type="button" class="gallery-action" data-review="list">Case list</button><button type="button" class="gallery-action" data-review="reasons" aria-pressed="false">Show all judge details</button></div>';
    panel.querySelector('.subgroup-head, .agent-subgroup-head').after(bar);
    var select = bar.querySelector('select');
    var lastSignature = '';
    function visible() { return all.filter(function (choice) { return !choice.hidden; }); }
    function current() { return visible().find(function (choice) { return choice.open; }); }
    function details(choice) { return choice ? Array.from(choice.querySelectorAll('.agent-judge-detail, .judge-analysis')) : []; }
    function refresh() {
      var items = visible(), opened = current(), index = items.indexOf(opened);
      panel.classList.toggle('review-reading', Boolean(opened) && panel.dataset.expanded !== 'true');
      var signature = items.map(function (choice) { return choice.id; }).join('|');
      if (signature !== lastSignature) {
        select.replaceChildren();
        var placeholder = document.createElement('option');placeholder.value = '';placeholder.textContent = 'Choose a case to compare';select.appendChild(placeholder);
        items.forEach(function (choice, i) {
          var option = document.createElement('option'); option.value = choice.id;
          option.textContent = (i + 1) + '. ' + choice.querySelector('.choice-title, .agent-choice-title').textContent;
          select.appendChild(option);
        });
        lastSignature = signature;
      }
      select.value = opened ? opened.id : '';
      bar.querySelector('.review-position').textContent = opened ? 'Case ' + (index + 1) + ' of ' + items.length : items.length + ' cases · browse without closing each one';
      bar.querySelector('[data-review="prev"]').disabled = index <= 0;
      bar.querySelector('[data-review="next"]').disabled = !items.length || index === items.length - 1;
      bar.querySelector('[data-review="next"]').textContent = opened ? 'Next →' : 'Start browsing →';
      bar.querySelector('[data-review="list"]').disabled = !opened;
      var reasons = details(opened), expanded = reasons.length > 0 && reasons.every(function (item) { return item.open; });
      var button = bar.querySelector('[data-review="reasons"]');button.disabled = !reasons.length;
      var hideReasons = panel.classList.contains('example-subgroup');
      if (button.hidden !== hideReasons) button.hidden = hideReasons;
      button.setAttribute('aria-pressed', String(expanded));button.textContent = expanded ? 'Hide judge details' : 'Show all judge details';
    }
    function navigate(choice) {
      if (!choice) return;
      panel.dataset.expanded = 'false';
      all.forEach(function (other) {
        if (other !== choice) { other.open = false; other.querySelectorAll('audio').forEach(function (audio) { audio.pause(); }); }
      });
      choice.open = true;
      window.VocaCases.load(choice);
      window.VocaCases.prefetch(panel);
      history.replaceState(null, '', '#' + choice.id);
      refresh();
      requestAnimationFrame(function () { bar.scrollIntoView({block: 'start', behavior: 'instant'}); });
    }
    select.addEventListener('change', function () { navigate(itemsByID(select.value)); });
    function itemsByID(id) { return visible().find(function (choice) { return choice.id === id; }); }
    bar.addEventListener('click', function (event) {
      var button = event.target.closest('[data-review]');if (!button) return;
      var items = visible(), opened = current(), index = items.indexOf(opened);
      if (button.dataset.review === 'prev') navigate(items[index - 1]);
      if (button.dataset.review === 'next') navigate(items[index + 1]);
      if (button.dataset.review === 'list') {
        all.forEach(function (choice) { choice.open = false; choice.querySelectorAll('audio').forEach(function (audio) { audio.pause(); }); });
        history.replaceState(null, '', '#' + panel.id);refresh();bar.scrollIntoView({block: 'start', behavior: 'instant'});
      }
      if (button.dataset.review === 'reasons') {
        var expand = button.getAttribute('aria-pressed') !== 'true';details(opened).forEach(function (item) { item.open = expand; });refresh();
      }
    });
    panel.addEventListener('toggle', refresh, true);
    document.addEventListener('case:loaded', function (event) { if (panel.contains(event.detail)) refresh(); });
    new MutationObserver(function () {
      refresh();
      if (!panel.closest('[hidden]') && panel.getBoundingClientRect().top < innerHeight + 500) window.VocaCases.prefetch(panel);
    }).observe(panel, {attributes:true, subtree:true, attributeFilter:['hidden']});
    refresh();
  });
})();
