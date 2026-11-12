/* Westport Family Homes — v1 Traditional. Header state, mobile menu, hero room crossfade. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var header = d.querySelector('.site-header');
  var hero = d.querySelector('[data-slideshow]');
  /* Preview hook: ?slide=0-3 opens the hero paused on that room. */
  var qs = new URLSearchParams(location.search);

  /* Header: transparent over the hero, solid cream once the hero has scrolled under it.
     The same observer pauses the slideshow while the hero is off screen. */
  var heroVisible = true;
  if (hero && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      heroVisible = entries[0].isIntersecting;
      if (header) header.classList.toggle('is-solid', !heroVisible);
      syncPause();
    }, { rootMargin: '-' + ((header && header.offsetHeight) || 90) + 'px 0px 0px 0px' }).observe(hero);
  } else if (header) {
    header.classList.add('is-solid');
  }

  /* Mobile menu */
  var toggle = d.querySelector('.menu-toggle');
  var menu = d.getElementById('menu');
  function setMenu(open) {
    if (!toggle || !menu) return;
    menu.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.menu-toggle__label').textContent = open ? 'Close' : 'Menu';
    root.classList.toggle('menu-open', open);
    if (open) { var first = menu.querySelector('a'); if (first) first.focus(); }
  }
  if (toggle && menu) {
    toggle.addEventListener('click', function () { setMenu(menu.hidden); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !menu.hidden) { setMenu(false); toggle.focus(); }
    });
    window.matchMedia('(min-width: 961px)').addEventListener('change', function (m) { if (m.matches) setMenu(false); });
  }

  /* Hero: four rooms of 5 Baldwin Place. The gold fill on the active segment is a 6s CSS
     animation; its animationend advances the room. Pausing that animation (tab hidden, hero off
     screen, or the Pause button) pauses the slideshow, so there is a single clock. */
  var userPaused = false;
  function syncPause() {
    if (hero) hero.classList.toggle('is-paused', userPaused || d.hidden || !heroVisible);
  }
  if (!hero) return;

  var slides = [].slice.call(hero.querySelectorAll('.hero__slide'));
  var caps = [].slice.call(hero.querySelectorAll('.hero__cap'));
  var segs = [].slice.call(hero.querySelectorAll('.hero__seg'));
  var pauseBtn = hero.querySelector('.hero__pause');
  var current = 0, pending = -1;

  function load(img) {
    if (img.dataset.srcset) {
      img.sizes = '100vw';
      img.srcset = img.dataset.srcset;
      img.src = img.dataset.src;
      img.removeAttribute('data-srcset');
      img.removeAttribute('data-src');
    }
  }
  function ready(img) { return img.complete && img.naturalWidth > 0; }

  function go(n) {
    var img = slides[n];
    load(img);
    if (!ready(img)) {
      // wait for the next room's photo before fading to it
      if (pending !== n) {
        pending = n;
        img.addEventListener('load', function () { if (pending === n) { pending = -1; go(n); } }, { once: true });
      }
      return;
    }
    if (pending !== n || !img.dataset.decoded) {
      // decode before fading so the crossfade never reveals a half-painted photo
      pending = n;
      var done = function () { img.dataset.decoded = '1'; if (pending === n) go(n); };
      if (img.decode) img.decode().then(done, done); else done();
      return;
    }
    pending = -1;
    current = n;
    slides.forEach(function (s, k) {
      s.classList.toggle('is-active', k === n);
      s.setAttribute('aria-hidden', k === n ? 'false' : 'true');
    });
    caps.forEach(function (c, k) { c.classList.toggle('is-active', k === n); });
    segs.forEach(function (s, k) {
      s.classList.remove('is-active');
      s.classList.toggle('is-done', k < n);
      s.setAttribute('aria-current', k === n ? 'true' : 'false');
    });
    void segs[n].offsetWidth; // restart the fill animation
    segs[n].classList.add('is-active');
  }

  segs.forEach(function (s, k) {
    s.addEventListener('click', function () { go(k); });
    s.querySelector('.hero__fill').addEventListener('animationend', function () {
      if (!reduce && s.classList.contains('is-active')) go((k + 1) % slides.length);
    });
  });

  if (pauseBtn) {
    if (reduce) pauseBtn.hidden = true;
    pauseBtn.addEventListener('click', function () {
      userPaused = !userPaused;
      pauseBtn.setAttribute('aria-pressed', String(userPaused));
      pauseBtn.textContent = userPaused ? 'Play' : 'Pause';
      syncPause();
    });
  }
  d.addEventListener('visibilitychange', syncPause);

  // Only the first room loads with the page; the other three load after everything else.
  function loadRest() { if (!reduce) slides.slice(1).forEach(load); }
  if (d.readyState === 'complete') loadRest(); else window.addEventListener('load', loadRest);
  var startAt = parseInt(qs.get('slide'), 10);
  if (startAt > 0 && startAt < slides.length) { userPaused = true; syncPause(); go(startAt); }
})();
