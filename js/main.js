document.addEventListener("DOMContentLoaded", () => {
  gsap.registerPlugin(ScrollTrigger);

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- Preloader ---------------- */
  const preloader = document.getElementById("preloader");
  if (preloader) {
    window.addEventListener("load", () => {
      setTimeout(() => preloader.classList.add("is-hidden"), 1100);
    });
    // Fallback in case load event is slow / cached
    setTimeout(() => preloader.classList.add("is-hidden"), 3200);
  }

  /* ---------------- Lenis smooth scroll ---------------- */
  let lenis;
  if (!reduceMotion && window.Lenis) {
    lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
    window.lenis = lenis;
  }

  /* ---------------- Header state ---------------- */
  const header = document.getElementById("siteHeader");
  ScrollTrigger.create({
    start: 60,
    end: 99999,
    onUpdate: (self) => {
      header.classList.toggle("is-scrolled", self.scroll() > 60);
    },
  });

  /* ---------------- Mobile nav ---------------- */
  const navToggle = document.getElementById("navToggle");
  const mobileNav = document.getElementById("mobileNav");
  navToggle.addEventListener("click", () => {
    const open = mobileNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", open);
  });
  mobileNav.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => {
      mobileNav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", false);
    })
  );

  /* ---------------- Hero entrance (plays on load, hero is the first thing shown) ---------------- */
  const heroTl = gsap.timeline({ delay: 0.4 });
  heroTl
    .to(".hero__eyebrow", { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" })
    .to(".hero__headline .reveal-line > span", {
      y: "0%",
      duration: 1,
      stagger: 0.12,
      ease: "power4.out",
    }, "-=0.4")
    .to(".hero__sub, .hero__actions", {
      opacity: 1, y: 0, duration: 0.9, ease: "power3.out", stagger: 0.1,
    }, "-=0.5");

  /* ---------------- Hero Ken Burns + scrim on scroll ---------------- */
  gsap.to("#heroImg", {
    scale: 1.28,
    ease: "none",
    scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true, invalidateOnRefresh: true },
  });
  gsap.to(".hero__content", {
    yPercent: 30,
    opacity: 0,
    ease: "none",
    scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true, invalidateOnRefresh: true },
  });

  /* ---------------- Generic reveals ---------------- */
  gsap.utils.toArray(".reveal-fade").forEach((el) => {
    gsap.to(el, {
      opacity: 1, y: 0, duration: 1, ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 88%" },
    });
  });

  gsap.utils.toArray(".reveal-up").forEach((el, i) => {
    gsap.to(el, {
      opacity: 1, y: 0, duration: 0.9, ease: "power3.out",
      delay: (i % 4) * 0.06,
      scrollTrigger: { trigger: el, start: "top 92%" },
    });
  });

  gsap.utils.toArray(".reveal-clip").forEach((el) => {
    gsap.to(el, {
      clipPath: "inset(0 0 0% 0)",
      duration: 1.1, ease: "power4.inOut",
      scrollTrigger: { trigger: el, start: "top 85%" },
    });
  });

  /* ---------------- Listing image parallax ---------------- */
  gsap.to(".listing__img--a img", {
    yPercent: -8, ease: "none",
    scrollTrigger: { trigger: ".listing", start: "top bottom", end: "bottom top", scrub: true },
  });
  gsap.to(".listing__img--b img", {
    yPercent: 10, ease: "none",
    scrollTrigger: { trigger: ".listing", start: "top bottom", end: "bottom top", scrub: true },
  });

  /* ---------------- Count-up stats ---------------- */
  gsap.utils.toArray(".stat__num").forEach((el) => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || "";
    const obj = { val: 0 };
    ScrollTrigger.create({
      trigger: el,
      start: "top 90%",
      once: true,
      onEnter: () => {
        gsap.to(obj, {
          val: target,
          duration: 1.6,
          ease: "power2.out",
          onUpdate: () => { el.textContent = Math.round(obj.val) + suffix; },
        });
      },
    });
  });

  /* ---------------- Portfolio grid entrance stagger ---------------- */
  gsap.utils.toArray(".home-card").forEach((el, i) => {
    gsap.fromTo(el, { opacity: 0, y: 40 }, {
      opacity: 1, y: 0, duration: 0.8, ease: "power3.out",
      delay: (i % 3) * 0.08,
      scrollTrigger: { trigger: el, start: "top 92%" },
    });
  });

  /* ---------------- Spotlight: native horizontal-scrolling gallery ---------------- */
  const spotlightWrap = document.querySelector(".spotlight__track-wrap");
  const spotlightPrev = document.getElementById("spotlightPrev");
  const spotlightNext = document.getElementById("spotlightNext");
  if (spotlightWrap && spotlightPrev && spotlightNext) {
    const scrollByPanel = (dir) => {
      const panel = spotlightWrap.querySelector(".spotlight__panel");
      const gap = parseFloat(getComputedStyle(document.querySelector(".spotlight__track")).gap) || 24;
      const amount = (panel ? panel.getBoundingClientRect().width : 400) + gap;
      spotlightWrap.scrollBy({ left: dir * amount, behavior: "smooth" });
    };
    spotlightPrev.addEventListener("click", () => scrollByPanel(-1));
    spotlightNext.addEventListener("click", () => scrollByPanel(1));

    const updateSpotlightNav = () => {
      const max = spotlightWrap.scrollWidth - spotlightWrap.clientWidth - 2;
      spotlightPrev.disabled = spotlightWrap.scrollLeft <= 2;
      spotlightNext.disabled = spotlightWrap.scrollLeft >= max;
    };
    spotlightWrap.addEventListener("scroll", updateSpotlightNav, { passive: true });
    window.addEventListener("resize", updateSpotlightNav);
    updateSpotlightNav();
  }

  /* ---------------- Accordions ---------------- */
  document.querySelectorAll(".acc-item").forEach((item) => {
    const trigger = item.querySelector(".acc-item__trigger");
    const panel = item.querySelector(".acc-item__panel");
    if (item.classList.contains("is-open")) {
      panel.style.height = "auto";
    }
    trigger.addEventListener("click", () => {
      const group = item.parentElement;
      const isOpen = item.classList.contains("is-open");

      group.querySelectorAll(".acc-item.is-open").forEach((openItem) => {
        if (openItem !== item) {
          const p = openItem.querySelector(".acc-item__panel");
          gsap.to(p, { height: 0, duration: 0.45, ease: "power2.inOut" });
          openItem.classList.remove("is-open");
        }
      });

      if (isOpen) {
        gsap.to(panel, { height: 0, duration: 0.45, ease: "power2.inOut" });
        item.classList.remove("is-open");
      } else {
        item.classList.add("is-open");
        gsap.set(panel, { height: "auto" });
        const h = panel.offsetHeight;
        gsap.fromTo(panel, { height: 0 }, { height: h, duration: 0.5, ease: "power2.inOut" });
      }
      ScrollTrigger.refresh();
    });
  });

  /* ---------------- Cinematic parallax ---------------- */
  gsap.to(".cinematic__img img", {
    yPercent: -12, ease: "none",
    scrollTrigger: { trigger: ".cinematic", start: "top bottom", end: "bottom top", scrub: true },
  });

  /* ---------------- Smooth anchor links ---------------- */
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const id = a.getAttribute("href");
      if (id.length > 1 && document.querySelector(id)) {
        e.preventDefault();
        const target = document.querySelector(id);
        if (lenis) lenis.scrollTo(target, { offset: -20 });
        else target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  window.addEventListener("resize", () => {
    clearTimeout(window.__wfhResize);
    window.__wfhResize = setTimeout(() => {
      ScrollTrigger.refresh();
    }, 250);
  });
});
