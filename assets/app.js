// Portfolio interactions. The page works without this file; it only adds behaviour.
(() => {
  const root = document.documentElement;
  root.classList.add("js");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const store = {
    get: k => { try { return localStorage.getItem(k); } catch { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode: ignore */ } },
  };

  // theme -----------------------------------------------------------------------------------------
  $(".theme-btn")?.addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    store.set("theme", root.dataset.theme);
  });

  // mobile menu -----------------------------------------------------------------------------------
  const menuBtn = $(".menu-btn"), menu = $("#menu");
  menuBtn?.addEventListener("click", () => {
    const open = menu.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", open);
  });
  $$("#menu a").forEach(a => a.addEventListener("click", () => { menu.classList.remove("open"); menuBtn?.setAttribute("aria-expanded", "false"); }));

  // scroll progress, nav border, active section -------------------------------------------------------
  const bar = $(".progress"), nav = $(".nav");
  const links = $$("#menu a");
  const sections = links.map(a => $(a.getAttribute("href"))).filter(Boolean);
  const onScroll = () => {
    const h = document.documentElement.scrollHeight - innerHeight;
    bar.style.width = `${h > 0 ? (scrollY / h) * 100 : 0}%`;
    nav.classList.toggle("scrolled", scrollY > 8);
    let current = null;
    for (const s of sections) if (s.getBoundingClientRect().top < innerHeight * 0.35) current = s.id;
    links.forEach(a => a.classList.toggle("active", a.getAttribute("href") === `#${current}`));
  };
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // rotating roles --------------------------------------------------------------------------------
  const roleEl = $(".role-text");
  if (roleEl && !reduced) {
    const roles = JSON.parse(roleEl.dataset.roles);
    let r = 0, i = roles[0].length, deleting = true;
    const tick = () => {
      const word = roles[r];
      if (deleting) {
        i--;
        if (i === 0) { deleting = false; r = (r + 1) % roles.length; }
      } else {
        i++;
        if (i === roles[r].length) { deleting = true; roleEl.textContent = roles[r]; return setTimeout(tick, 2200); }
      }
      roleEl.textContent = (deleting ? word : roles[r]).slice(0, i);
      setTimeout(tick, deleting ? 40 : 75);
    };
    setTimeout(tick, 2400);
  }

  // count-up numbers --------------------------------------------------------------------------------
  const fmt = (v, d) => v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  const countUp = el => {
    const target = parseFloat(el.dataset.count), d = parseInt(el.dataset.decimals || "0", 10);
    if (reduced) { el.textContent = fmt(target, d); return; }
    const t0 = performance.now(), dur = 1400;
    const step = now => {
      const p = Math.min((now - t0) / dur, 1), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(target * eased, d);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  // reveal on scroll (+ counters and bars when they appear) -------------------------------------------
  const seen = new IntersectionObserver(entries => {
    for (const en of entries) {
      if (!en.isIntersecting) continue;
      en.target.classList.add("in");
      $$("[data-count]", en.target).forEach(countUp);
      if (en.target.matches("[data-count]")) countUp(en.target);
      $$("[data-bars]", en.target).forEach(b => b.classList.add("in"));
      seen.unobserve(en.target);
    }
  }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
  $$(".reveal").forEach(el => seen.observe(el));

  // project filters --------------------------------------------------------------------------------
  const chips = $$(".chip"), cards = $$("#projects .card");
  chips.forEach(chip => chip.addEventListener("click", () => {
    const f = chip.dataset.filter;
    chips.forEach(c => { c.classList.toggle("active", c === chip); c.setAttribute("aria-pressed", c === chip); });
    cards.forEach(card => {
      const show = f === "all" || card.dataset.cat.split(" ").includes(f);
      card.classList.toggle("hidden", !show);
      if (show) card.classList.add("in");
    });
  }));

  // subtle tilt on cards (pointer devices only) --------------------------------------------------------
  if (!reduced && matchMedia("(hover: hover)").matches) {
    cards.forEach(card => {
      card.addEventListener("pointermove", ev => {
        const b = card.getBoundingClientRect();
        const x = (ev.clientX - b.left) / b.width - 0.5, y = (ev.clientY - b.top) / b.height - 0.5;
        card.style.transform = `perspective(900px) rotateX(${-y * 4}deg) rotateY(${x * 5}deg) translateY(-4px)`;
      });
      card.addEventListener("pointerleave", () => { card.style.transform = ""; });
    });
  }

  // dialogs -----------------------------------------------------------------------------------------
  $$("[data-open]").forEach(btn => btn.addEventListener("click", () => {
    const d = document.getElementById(btn.dataset.open);
    if (d?.showModal) d.showModal(); else d?.setAttribute("open", "");
  }));
  $$("dialog").forEach(d => d.addEventListener("click", ev => {   // click on the backdrop closes
    const b = d.getBoundingClientRect();
    if (ev.clientX < b.left || ev.clientX > b.right || ev.clientY < b.top || ev.clientY > b.bottom) d.close();
  }));

  // CV dropdown -------------------------------------------------------------------------------------
  const dd = $(".dropdown"), ddBtn = $(".dropdown > button");
  ddBtn?.addEventListener("click", ev => {
    ev.stopPropagation();
    const open = dd.classList.toggle("open");
    ddBtn.setAttribute("aria-expanded", open);
  });
  document.addEventListener("click", ev => { if (dd && !dd.contains(ev.target)) { dd.classList.remove("open"); ddBtn?.setAttribute("aria-expanded", "false"); } });
  document.addEventListener("keydown", ev => { if (ev.key === "Escape") { dd?.classList.remove("open"); menu?.classList.remove("open"); } });

  // skill tabs (arrow keys move between tabs) -----------------------------------------------------------
  const tabs = $$(".tab");
  const select = t => {
    tabs.forEach(x => { x.setAttribute("aria-selected", x === t); x.tabIndex = x === t ? 0 : -1; });
    $$(".tab-panel").forEach(p => { p.hidden = p.id !== t.getAttribute("aria-controls"); });
  };
  tabs.forEach((t, i) => {
    t.tabIndex = i === 0 ? 0 : -1;
    t.addEventListener("click", () => select(t));
    t.addEventListener("keydown", ev => {
      const k = { ArrowRight: 1, ArrowLeft: -1 }[ev.key];
      if (k) { const n = tabs[(i + k + tabs.length) % tabs.length]; select(n); n.focus(); }
    });
  });

  // copy e-mail -------------------------------------------------------------------------------------
  const toast = $(".toast");
  const say = msg => { toast.textContent = msg; toast.classList.add("show"); setTimeout(() => toast.classList.remove("show"), 1800); };
  $$("[data-copy]").forEach(b => b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); say("E-mail address copied"); }
    catch { location.href = `mailto:${b.dataset.copy}`; }
  }));
})();
