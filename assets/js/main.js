(function bootHome() {
  function run() {
    initHeroSlider();
    initReveals();
    initForms();
    initParallaxBands();
    initGoogleReviewsCarousel();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();

function initGoogleReviewsCarousel() {
  const track = document.getElementById('bg-review-track');
  const dotsWrap = document.getElementById('bg-review-dots');
  const prev = document.getElementById('bg-review-prev');
  const next = document.getElementById('bg-review-next');
  if (!track || !dotsWrap || !prev || !next) return;

  const cards = Array.from(track.children);
  if (!cards.length) return;

  let index = 0;

  function perView() {
    if (window.innerWidth < 760) return 1;
    if (window.innerWidth < 960) return 2;
    if (window.innerWidth < 1100) return 1;
    return 2;
  }

  function pageCount() {
    return Math.max(1, Math.ceil(cards.length / perView()));
  }

  function renderDots() {
    dotsWrap.innerHTML = '';
    const pages = pageCount();
    for (let i = 0; i < pages; i += 1) {
      const dot = document.createElement('button');
      dot.type = 'button';
      dot.className = 'bg-review-dot' + (i === index ? ' is-active' : '');
      dot.setAttribute('aria-label', 'Go to review set ' + (i + 1));
      dot.addEventListener('click', () => {
        index = i;
        update();
      });
      dotsWrap.appendChild(dot);
    }
  }

  function update() {
    const pages = pageCount();
    if (index > pages - 1) index = pages - 1;
    if (index < 0) index = 0;
    const sample = cards[0];
    const gap = 16;
    const width = sample ? sample.getBoundingClientRect().width : 0;
    const offset = index * (width + gap) * perView();
    track.style.transform = 'translateX(' + (-offset) + 'px)';
    Array.from(dotsWrap.children).forEach((dot, dotIndex) => {
      dot.classList.toggle('is-active', dotIndex === index);
    });
    prev.disabled = index === 0;
    next.disabled = index === pages - 1;
  }

  prev.addEventListener('click', () => {
    index -= 1;
    update();
  });
  next.addEventListener('click', () => {
    index += 1;
    update();
  });
  window.addEventListener('resize', () => {
    renderDots();
    update();
  });

  renderDots();
  update();
}

function initReveals() {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cycle = ['reveal--up', 'reveal--left', 'reveal--right', 'reveal--down'];
  let cycleIndex = 0;

  const autoSelectors = [
    '.service-panel',
    '.service-aside__card',
    '.service-tail .service-panel',
    '.project-mirror',
    '.project-composite',
    '.project-shot',
    '.project-case__cta',
    '.project-case__intro',
    '.project-case__section',
    '.area-local-shot',
    '.bg-google-reviews-showcase',
    '.bg-map-panel',
    '.bg-review-card',
    '.stat-row > div',
    '.feature-list > li',
    '.page-hero__copy',
    '.faq',
    '.split > .prose',
    '.split > .form-card',
    '.hero__copy',
    '.hero-card:not(.hero-card--bridge)',
    '.project-card',
    '.service-tile',
    '.media-stage',
    '.related-links',
    '.cta-band__copy',
    '.cta-band__form',
    '.reveal',
  ];

  function hasDirection(el) {
    return Array.from(el.classList).some((name) => name.startsWith('reveal--'));
  }

  function nextCycleDirection() {
    const dir = cycle[cycleIndex % cycle.length];
    cycleIndex += 1;
    return dir;
  }

  function assignDirection(el) {
    if (hasDirection(el) || el.classList.contains('reveal--fade')) return;

    const parent = el.parentElement;
    if (!parent) {
      el.classList.add('reveal--up');
      return;
    }

    const idx = Array.from(parent.children).indexOf(el);

    if (
      parent.classList.contains('split')
      || parent.classList.contains('cta-band__inner')
      || parent.classList.contains('service-photos-row')
    ) {
      el.classList.add(idx === 0 ? 'reveal--left' : 'reveal--right');
      return;
    }

    if (parent.classList.contains('service-layout')) {
      el.classList.add(el.classList.contains('service-aside') ? 'reveal--right' : 'reveal--left');
      return;
    }

    if (parent.classList.contains('service-main')) {
      el.classList.add(cycle[idx % cycle.length]);
      return;
    }

    if (
      parent.classList.contains('service-grid')
      || parent.classList.contains('project-grid')
      || parent.classList.contains('project-more__grid')
      || parent.classList.contains('related-links-grid')
    ) {
      el.classList.add(cycle[idx % cycle.length]);
      return;
    }

    if (el.classList.contains('project-mirror')) {
      el.classList.add(el.classList.contains('project-mirror--flip') ? 'reveal--right' : 'reveal--left');
      return;
    }

    el.classList.add(nextCycleDirection());
  }

  function staggerDelay(el) {
    const parent = el.parentElement;
    if (!parent) return 0;

    const staggerParents = [
      'service-main',
      'service-grid',
      'project-grid',
      'project-more__grid',
      'related-links-grid',
      'feature-list',
      'stat-row',
      'bg-review-carousel-track',
    ];

    if (!staggerParents.some((name) => parent.classList.contains(name))) return 0;

    const peers = Array.from(parent.children).filter((child) => child.classList.contains('reveal'));
    const peerIndex = peers.indexOf(el);
    return peerIndex > -1 ? peerIndex * 140 : 0;
  }

  function prepare(el) {
    if (!el || el.closest('.hero-stage')) return;

    const fadeOnly = el.matches('.form-card--sticky, .service-aside .form-card--sticky');
    if (!el.classList.contains('reveal')) el.classList.add('reveal');

    if (fadeOnly) {
      el.classList.add('reveal--fade');
    } else {
      assignDirection(el);
    }

    const delay = staggerDelay(el);
    if (delay) el.style.setProperty('--reveal-delay', delay + 'ms');
  }

  const seen = new Set();
  autoSelectors.forEach((selector) => {
    document.querySelectorAll(selector).forEach((el) => {
      if (seen.has(el)) return;
      seen.add(el);
      prepare(el);
    });
  });

  const reveals = document.querySelectorAll('.reveal');
  if (reducedMotion) {
    reveals.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -6% 0px' });

    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-visible'));
  }
}

function initForms() {
  document.querySelectorAll('form[data-bg-form]').forEach((form) => {
    const pageField = form.querySelector('[name="page"]');
    if (pageField) pageField.value = location.pathname;

    const phone = form.querySelector('[name="phone"]');
    if (!phone) return;

    phone.addEventListener('input', () => {
      phone.setCustomValidity('');
    });

    form.addEventListener('submit', (event) => {
      const name = form.querySelector('[name="name"]');
      if (name && !name.value.trim()) {
        name.value = 'Not provided';
      }

      const digits = phone.value.replace(/\D/g, '');
      if (digits.length < 10) {
        event.preventDefault();
        phone.setCustomValidity('Enter a valid phone number with at least 10 digits.');
        phone.reportValidity();
        return;
      }
      phone.setCustomValidity('');
    });
  });
}

function applySlideBg(bg) {
  if (!bg || bg.dataset.bgLoaded) return;
  const url = bg.getAttribute('data-bg');
  if (!url) return;
  bg.style.backgroundImage = `url("${url}")`;
  bg.dataset.bgLoaded = '1';
}

function initHeroSlider() {
  const slides = document.querySelectorAll('.hero-slide');
  if (slides.length < 2) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (document.documentElement.dataset.heroSlider === '1') return;
  document.documentElement.dataset.heroSlider = '1';

  let current = 0;
  let slideInterval = null;

  function goTo(index) {
    const prevBg = slides[current].querySelector('.hero-slide-bg');
    slides[current].classList.remove('active');
    if (prevBg) {
      prevBg.style.animation = 'none';
      void prevBg.offsetWidth;
      prevBg.style.animation = '';
    }

    current = (index + slides.length) % slides.length;
    slides[current].classList.add('active');

    const newBg = slides[current].querySelector('.hero-slide-bg');
    applySlideBg(newBg);
    if (newBg) {
      newBg.style.animation = 'none';
      void newBg.offsetWidth;
      newBg.style.animation = '';
    }
  }

  function startSlider() {
    if (slideInterval) clearInterval(slideInterval);
    slideInterval = setInterval(() => goTo(current + 1), 6000);
  }

  startSlider();

  const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 1500));
  idle(() => applySlideBg(slides[1]?.querySelector('.hero-slide-bg[data-bg]')));

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      if (slideInterval) clearInterval(slideInterval);
      slideInterval = null;
    } else {
      startSlider();
    }
  });
}

function initParallaxBands() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const bands = document.querySelectorAll('[data-parallax-band]');
  if (!bands.length) return;

  let ticking = false;

  function update() {
    ticking = false;
    const vh = Math.max(window.innerHeight, 1);

    bands.forEach((band) => {
      const img = band.querySelector('.cta-band__bg img');
      if (!img) return;

      const rect = band.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > vh) return;

      const range = vh + band.offsetHeight;
      const progress = Math.max(0, Math.min(1, (vh - rect.top) / range));
      const maxShift = band.offsetHeight * 0.24;
      const shift = Math.round((progress - 0.5) * 2 * maxShift);
      img.style.setProperty('--bg-shift', `${shift}px`);
    });
  }

  function queue() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  }

  window.addEventListener('scroll', queue, { passive: true });
  window.addEventListener('resize', queue, { passive: true });
  queue();
}
