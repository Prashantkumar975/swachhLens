/* =========================================================
 * SwachhLens — Hero Typewriter Animation
 * ---------------------------------------------------------
 * Animates the hero headline word-by-word, then types out
 * the accent word ("report.") letter by letter with a
 * blinking cursor. Pure CSS + minimal JS, no dependencies.
 *
 * The h1 must have:
 *   data-hero-phrase="A cleaner city starts with one report."
 *   data-hero-accent="report."
 * ========================================================= */
(function () {
  var root = document.querySelector('[data-hero-type]');
  if (!root) return;

  var textEl = root.querySelector('[data-hero-type-text]');
  var accentEl = root.querySelector('[data-hero-type-accent]');
  if (!textEl || !accentEl) return;

  var phrase = root.getAttribute('data-hero-phrase') || 'A cleaner city starts with one report.';
  var accent = root.getAttribute('data-hero-accent') || 'report.';

  var accentIdx = phrase.indexOf(accent);
  if (accentIdx < 0) accentIdx = phrase.length;
  var before = phrase.slice(0, accentIdx);

  // Split the "before" part into words
  var words = before.split(/\s+/).filter(Boolean);
  var delay = 0;
  var wordDelay = 180; // ms between words

  // Animate words appearing one by one
  words.forEach(function (word, i) {
    setTimeout(function () {
      var span = document.createElement('span');
      span.className = 'hero-word';
      span.textContent = word;
      textEl.appendChild(span);
      textEl.appendChild(document.createTextNode('\u00A0')); // non-breaking space
    }, delay);
    delay += wordDelay;
  });

  // After all words appear, start typing the accent
  setTimeout(function () {
    var chars = accent.split('');
    var charIdx = 0;
    var typeInterval = setInterval(function () {
      if (charIdx < chars.length) {
        accentEl.textContent += chars[charIdx];
        charIdx++;
      } else {
        clearInterval(typeInterval);
      }
    }, 120); // typing speed
  }, delay + 200);
})();
