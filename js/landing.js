/* =====================================================================
 * SwachhLens — landing page (index.html)
 * ---------------------------------------------------------------------
 * Wires navigation, scroll-triggered IntersectionObserver reveals,
 * staggered children, marquee, animated counters, FAQ accordion,
 * and the mobile menu.
 * ===================================================================== */
(function () {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- Session-aware nav links ---------------- */
  (function syncNavLinks() {
    try {
      const s = JSON.parse(localStorage.getItem('swachlens.session') || 'null');
      if (!s || !s.authToken) return;
      const ROLE_PATHS = { USER: 'citizen-dashboard.html', EMPLOYEE: 'employee-dashboard.html' };
      const dashPath = ROLE_PATHS[s.role] || 'citizen-dashboard.html';
      const dashPathFull = new URL(dashPath, location.href).href;
      // Update nav buttons
      document.querySelectorAll('.lv-nav a[href="citizen-login.html"], .lv-nav a[href="citizen-register.html"]').forEach(a => {
        a.textContent = 'Dashboard';
        a.href = dashPathFull;
        a.removeAttribute('data-i18n');
      });
      // Update hero CTA
      document.querySelectorAll('.lv-hero a[href="citizen-login.html"]').forEach(a => {
        a.href = dashPathFull;
      });
      // Update mobile menu + CTA + footer — ALL remaining login/register links
      document.querySelectorAll('a[href="citizen-login.html"], a[href="citizen-register.html"]').forEach(a => {
        a.textContent = 'Dashboard';
        a.href = dashPathFull;
        a.removeAttribute('data-i18n');
      });
    } catch {}
  })();

  /* ---------------- Navigation ---------------- */
  const topnav = document.getElementById('topnav');
  const onScroll = () => {
    topnav.classList.toggle('is-scrolled', window.scrollY > 24);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Fade nav in
  if (!reduceMotion) {
    topnav.style.opacity = '0';
    topnav.style.transform = 'translateY(-10px)';
    topnav.style.transition = 'opacity 0.5s ease, transform 0.5s ease, background 0.3s, border-color 0.3s';
    setTimeout(() => {
      topnav.style.opacity = '1';
      topnav.style.transform = 'none';
    }, 200);
  }

  const burger = document.querySelector('[data-menu-btn]');
  const mobileMenu = document.querySelector('[data-mobile-menu]');
  const toggleMenu = (open) => {
    if (!mobileMenu) return;
    const isOpen = typeof open === 'boolean' ? open : !mobileMenu.classList.contains('is-open');
    mobileMenu.classList.toggle('is-open', isOpen);
    if (burger) {
      burger.classList.toggle('is-open', isOpen);
      burger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }
    document.body.classList.toggle('landing-menu-open', isOpen);
  };
  if (burger) burger.addEventListener('click', () => toggleMenu());
  mobileMenu && mobileMenu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => toggleMenu(false)));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggleMenu(false); });
  document.addEventListener('click', (e) => {
    if (mobileMenu && mobileMenu.classList.contains('is-open') && !mobileMenu.contains(e.target) && !(burger && burger.contains(e.target))) toggleMenu(false);
  });

  /* ---------------- IntersectionObserver-driven reveals ---------------- */
  function observeReveals() {
    const els = document.querySelectorAll('.lv-reveal, .lv-stagger, .lv-imgwrap, .lv-ai__bar');
    if (!('IntersectionObserver' in window) || reduceMotion) {
      els.forEach((el) => el.classList.add('in'));
      document.querySelectorAll('[data-count]').forEach(runCounter);
      document.querySelectorAll('.bar-fill').forEach((f) => (f.style.transform = 'scaleX(1)'));
      return;
    }

    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          el.classList.add('in');
          el.querySelectorAll && el.querySelectorAll('.bar-fill').forEach((f) => (f.style.transform = 'scaleX(1)'));
          el.querySelectorAll && el.querySelectorAll('[data-count]').forEach(runCounter);
          obs.unobserve(el);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -6% 0px'
    });

    els.forEach((el) => obs.observe(el));

    // Standalone counters
    document.querySelectorAll('[data-count]').forEach((el) => {
      if (!el.closest('.lv-reveal, .lv-stagger, .lv-imgwrap')) obs.observe(el);
    });
  }

  /* ---------------- Live stats from backend ---------------- */
  async function loadLiveStats() {
    try {
      const base = window.SW_CONFIG && window.SW_CONFIG.API_URL;
      if (!base) return;
      const res = await fetch(base + '/reports/public-stats');
      if (!res.ok) return;
      const data = await res.json();
      // Update stat numbers from backend
      const statEls = document.querySelectorAll('.lv-stat__no[data-stat-key]');
      statEls.forEach((el) => {
        const key = el.dataset.statKey;
        const val = data[key];
        if (val !== undefined && val !== null) {
          el.dataset.count = val;
          el.textContent = '0';
        }
      });
    } catch (err) {
      // Silently fall back to hardcoded values
    }
  }
  loadLiveStats();

  /* ---------------- Animated counters ---------------- */
  function runCounter(el) {
    if (el.dataset.counted) return;
    el.dataset.counted = '1';
    const target = (el.dataset.count !== undefined && parseFloat(el.dataset.count))
      || parseFloat(el.textContent.replace(/[^\d.]/g, '')) || 0;
    const hasDecimal = String(el.dataset.count || '').includes('.');
    const suffix = el.querySelector('small') ? el.querySelector('small').outerHTML : '';
    const dur = 1800;
    const start = performance.now();
    function tick(now) {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 4);
      const val = target * eased;
      if (hasDecimal) {
        el.textContent = val.toFixed(1);
      } else {
        el.textContent = Math.round(val).toLocaleString();
      }
      if (suffix) el.insertAdjacentHTML('beforeend', suffix);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* ---------------- FAQ accordion — close others when one opens ---------------- */
  document.querySelectorAll('.lv-faq__item').forEach((item) => {
    item.addEventListener('toggle', () => {
      if (item.open) {
        document.querySelectorAll('.lv-faq__item[open]').forEach((other) => {
          if (other !== item) other.open = false;
        });
      }
    });
  });

  /* ---------------- Hero parallax floating icons + scroll fade ---------------- */
  if (!reduceMotion) {
    const heroContent = document.querySelector('.lv-hero__content');
    const heroSection = document.querySelector('.lv-hero');
    const floats = document.querySelectorAll('.lv-float-icon');

    let heroRaf = null;
    window.addEventListener('scroll', () => {
      if (heroRaf) return;
      heroRaf = requestAnimationFrame(() => {
        const y = window.scrollY;
        const heroH = heroSection ? heroSection.offsetHeight : 0;
        
        // Parallax floating icons at different speeds
        floats.forEach((icon, i) => {
          const speed = 0.03 + (i % 3) * 0.02;
          icon.style.transform = `translateY(${y * speed}px) rotate(${(i % 2 === 0 ? 1 : -1) * y * 0.01}deg)`;
        });
        
        // Fade out hero content as user scrolls past
        if (heroContent) {
          const fadeStart = heroH * 0.35;
          const fadeEnd = heroH * 0.85;
          if (y > fadeStart) {
            const progress = Math.min(1, (y - fadeStart) / (fadeEnd - fadeStart));
            heroContent.style.opacity = 1 - progress * 0.65;
            heroContent.style.transform = `translateY(${-progress * 18}px) scale(${1 - progress * 0.02})`;
          } else {
            heroContent.style.opacity = 1;
            heroContent.style.transform = 'none';
          }
        }
        heroRaf = null;
      });
    }, { passive: true });
  }

  /* ---------------- Session-aware CTA ---------------- */
  // Removed: session-aware redirect was hijacking Register button href

  observeReveals();

  /* ---------------- Touch-friendly: active state feedback ---------------- */
  // Only apply transform to non-animated interactive elements (not buttons with CSS animations)
  document.querySelectorAll('.lv-role-card, .lv-product, .lv-faq__q, .lv-compare__col, .lv-stat').forEach((el) => {
    el.addEventListener('touchstart', () => {
      el.style.transition = 'transform 0.15s ease';
      el.style.transform = 'scale(0.97)';
    }, { passive: true });
    const reset = () => {
      el.style.transform = '';
      el.style.transition = '';
    };
    el.addEventListener('touchend', reset, { passive: true });
    el.addEventListener('touchcancel', reset, { passive: true });
  });

  /* ---------------- Stats: tap-to-expand + swipe dots ---------------- */
  const statsContainer = document.getElementById('lvStats');
  if (statsContainer) {
    const statBtns = statsContainer.querySelectorAll('.lv-stat');
    const dotsContainer = document.getElementById('statsDots');
    const dots = dotsContainer ? dotsContainer.querySelectorAll('span') : [];

    // Tap to expand/collapse stat detail
    statBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const wasExpanded = btn.getAttribute('aria-expanded') === 'true';
        // Close all others
        statBtns.forEach((b) => b.setAttribute('aria-expanded', 'false'));
        // Toggle clicked
        btn.setAttribute('aria-expanded', wasExpanded ? 'false' : 'true');
        // Fill in detail text from data attribute
        const detail = btn.querySelector('.lv-stat__detail');
        if (detail && !detail.textContent) {
          detail.textContent = btn.dataset.statDetail || '';
        }
      });
    });

    // Close expanded stat when clicking outside
    document.addEventListener('click', (e) => {
      if (!statsContainer.contains(e.target)) {
        statBtns.forEach((b) => b.setAttribute('aria-expanded', 'false'));
      }
    });

    // Keyboard: Enter/Space to toggle
    statBtns.forEach((btn) => {
      btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          btn.click();
        }
      });
    });

    // Mobile: swipe indicator dots
    function updateStatsDots() {
      if (!dots.length) return;
      const scrollLeft = statsContainer.scrollLeft;
      const cardWidth = statBtns[0] ? statBtns[0].offsetWidth + 12 : 200;
      const activeIdx = Math.round(scrollLeft / cardWidth);
      dots.forEach((dot, i) => {
        dot.classList.toggle('is-active', i === activeIdx);
      });
    }

    statsContainer.addEventListener('scroll', updateStatsDots, { passive: true });
    updateStatsDots();

    // Touch swipe on mobile
    if (window.matchMedia('(max-width: 640px)').matches) {
      let startX = 0;
      let isDragging = false;
      statsContainer.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        isDragging = false;
      }, { passive: true });
      statsContainer.addEventListener('touchmove', (e) => {
        const diff = Math.abs(e.touches[0].clientX - startX);
        if (diff > 10) isDragging = true;
      }, { passive: true });
      statsContainer.addEventListener('touchend', (e) => {
        if (!isDragging) return; // it was a tap, not a swipe
        const diff = startX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 40) {
          const cardWidth = statBtns[0] ? statBtns[0].offsetWidth + 12 : 200;
          const dir = diff > 0 ? 1 : -1;
          statsContainer.scrollBy({ left: cardWidth * dir, behavior: 'smooth' });
        }
      }, { passive: true });
    }
  }

  /* ---------------- Mobile: swipeable pipeline ---------------- */
  if (window.matchMedia('(max-width: 640px)').matches) {
    const rail = document.querySelector('.lv-pipeline__rail');
    if (rail) {
      let startX = 0;
      rail.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
      rail.addEventListener('touchend', (e) => {
        const diff = startX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 50) {
          const current = rail.scrollLeft;
          rail.scrollTo({ left: current + (diff > 0 ? 200 : -200), behavior: 'smooth' });
        }
      }, { passive: true });
    }
  }
})();
