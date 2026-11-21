/* SparRadar FX (v162, Tiry 21.11., Skill „modern-awwwards-web-design“)
   Liegt nach app.js und ändert nur Bewegung und Tiefe – keine App-Logik.
   1 WebGL-Shader-Hintergrund (Aurora mit Körnung, steht still – Tiry 21.11.)
   2 Lenis: träges, weiches Scrollen (nur PC mit Maus)
   3 Eigener Cursor mit Text („Ansehen“, „Öffnen“) – nur PC
   4 Magnetische Knöpfe mit elastischem Nachfedern – nur PC
   5 Reveal: Karten/Flächen erscheinen per Clip-Path-Maske, versetzt, mit leichter 3D-Drehung
   6 Kinetic Typography: Überschriften fahren Wort für Wort aus einer Maske, ziehen beim Scrollen zusammen
   Bei „weniger Bewegung“: nur ein ruhiges Standbild des Hintergrunds, sonst nichts. */
(() => {
  "use strict";
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const FINE = matchMedia("(hover:hover) and (pointer:fine)").matches;
  const G = window.gsap, ST = window.ScrollTrigger;
  const root = document.documentElement;
  if (G && ST) G.registerPlugin(ST);
  root.classList.add("fx");
  if (FINE) root.classList.add("fx-fine");

  /* ---------- 1 Shader-Hintergrund ---------- */
  (function shader() {
    const cv = document.createElement("canvas");
    cv.id = "fxbg"; cv.setAttribute("aria-hidden", "true");
    const gl = cv.getContext("webgl", { alpha: false, antialias: false, depth: false, powerPreference: "low-power" });
    if (!gl) return;
    const vs = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    const fs = `precision mediump float;
uniform vec2 r;uniform float t;uniform vec2 m;uniform float d;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);vec2 u=f*f*(3.-2.*f);
 return mix(mix(h(i),h(i+vec2(1.,0.)),u.x),mix(h(i+vec2(0.,1.)),h(i+vec2(1.,1.)),u.x),u.y);}
float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p=p*2.03+vec2(1.7,9.2);a*=.5;}return v;}
void main(){
 vec2 uv=gl_FragCoord.xy/r;vec2 p=uv*vec2(r.x/r.y,1.)*1.5;float tt=t*.035;
 vec2 mm=(m-.5)*vec2(.9,-.9);
 vec2 q=vec2(fbm(p+tt+mm*.4),fbm(p+vec2(5.2,1.3)-tt));
 vec2 w=vec2(fbm(p+2.4*q+vec2(1.7,9.2)+tt*.6+mm),fbm(p+2.4*q+vec2(8.3,2.8)-tt*.4));
 float f=fbm(p+2.6*w);
 vec3 base=mix(vec3(.89,.97,.92),vec3(.016,.05,.033),d);
 vec3 c1=mix(vec3(.13,.78,.37),vec3(.10,.62,.30),d);
 vec3 c2=mix(vec3(.05,.71,.66),vec3(.04,.50,.47),d);
 vec3 c3=mix(vec3(1.,.86,.25),vec3(.62,.46,.05),d);
 vec3 c4=mix(vec3(.62,.88,.20),vec3(.20,.45,.10),d);
 vec3 col=base;
 col=mix(col,c1,smoothstep(.30,.95,f)*mix(.78,.62,d));
 col=mix(col,c2,smoothstep(.35,.95,w.x)*mix(.58,.50,d));
 col=mix(col,c4,smoothstep(.55,.95,q.y)*mix(.35,.22,d));
 col=mix(col,c3,smoothstep(.62,.98,w.y*f*1.7)*mix(.55,.30,d));
 col=mix(col,base,mix(.18,.10,d)+.12*smoothstep(.2,.0,abs(uv.x-.5)-.25));
 col+=(h(gl_FragCoord.xy+fract(t)*91.)-.5)*mix(.045,.06,d);
 gl_FragColor=vec4(col,1.);}`;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null; };
    const v = sh(gl.VERTEX_SHADER, vs), f = sh(gl.FRAGMENT_SHADER, fs);
    if (!v || !f) return;
    const pr = gl.createProgram(); gl.attachShader(pr, v); gl.attachShader(pr, f); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return;
    gl.useProgram(pr);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const U = k => gl.getUniformLocation(pr, k), uR = U("r"), uT = U("t"), uM = U("m"), uD = U("d");
    const dk = matchMedia("(prefers-color-scheme: dark)");
    const SCALE = FINE ? .5 : .35; // innen klein rechnen, CSS skaliert weich hoch
    const size = () => { cv.width = Math.max(2, Math.round(innerWidth * SCALE)); cv.height = Math.max(2, Math.round(innerHeight * SCALE)); gl.viewport(0, 0, cv.width, cv.height); };
    size(); addEventListener("resize", size, { passive: true });
    document.body.prepend(cv);
    root.classList.add("fx-gl");
    // Tiry 21.11.: Hintergrund steht still – ein Bild, neu gezeichnet nur bei Größen- oder Hell/Dunkel-Wechsel
    const draw = () => {
      gl.uniform2f(uR, cv.width, cv.height); gl.uniform1f(uT, 20.); gl.uniform2f(uM, .5, .5);
      gl.uniform1f(uD, root.dataset.theme === "dark" || (root.dataset.theme !== "light" && dk.matches) ? 1 : 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    };
    draw();
    addEventListener("resize", () => requestAnimationFrame(draw), { passive: true });
    dk.addEventListener?.("change", draw);
    new MutationObserver(draw).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    cv.addEventListener("webglcontextlost", e => { e.preventDefault(); cv.remove(); root.classList.remove("fx-gl"); });
  })();

  if (RM || !G) return;

  /* ---------- 2 Lenis (PC) ---------- */
  if (FINE && window.Lenis && ST) {
    const lenis = new Lenis({ lerp: .11, wheelMultiplier: 1, smoothWheel: true,
      prevent: node => !!(node.closest && node.closest(".sheet,.scrim,#qSugg,.sugg,.lightbox,#lightbox,textarea,select")) });
    lenis.on("scroll", ST.update);
    G.ticker.add(t => lenis.raf(t * 1000)); G.ticker.lagSmoothing(0);
    // offenes Fenster: Seite dahinter steht still
    const open = () => [...document.querySelectorAll(".scrim")].some(s => !s.hidden && s.getClientRects().length && getComputedStyle(s).visibility !== "hidden" && getComputedStyle(s).display !== "none");
    let was = null;
    new MutationObserver(() => { const o = open(); if (o !== was) { was = o; o ? lenis.stop() : lenis.start(); } })
      .observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "class", "style"] });
    window.__lenis = lenis;
  }

  /* ---------- 3 Eigener Cursor (PC) ---------- */
  if (FINE) {
    const dot = document.createElement("div"), ring = document.createElement("div");
    dot.id = "fxdot"; ring.id = "fxring"; dot.setAttribute("aria-hidden", "true"); ring.setAttribute("aria-hidden", "true");
    ring.innerHTML = "<span></span>"; document.body.append(ring, dot);
    const lab = ring.firstChild;
    const dx = G.quickTo(dot, "x", { duration: .08, ease: "power3" }), dy = G.quickTo(dot, "y", { duration: .08, ease: "power3" });
    const rx = G.quickTo(ring, "x", { duration: .5, ease: "power3" }), ry = G.quickTo(ring, "y", { duration: .5, ease: "power3" });
    let mode = "";
    addEventListener("pointermove", e => {
      if (e.pointerType !== "mouse") return;
      root.classList.add("fx-cur");
      dx(e.clientX); dy(e.clientY); rx(e.clientX); ry(e.clientY);
      const t = e.target.closest ? e.target : null;
      const m = !t ? "" : t.closest(".kv") ? "Öffnen" : t.closest("button,a,[role=tab],select,label,summary,.chip") ? "btn" : t.closest(".grid>.card,.witem,.drow[data-detail]") ? "Ansehen" : t.closest("input,textarea") ? "text" : "";
      if (m !== mode) { mode = m; ring.dataset.m = m === "Öffnen" || m === "Ansehen" ? "label" : m; lab.textContent = m === "Öffnen" || m === "Ansehen" ? m : ""; }
    }, { passive: true });
    document.addEventListener("pointerleave", () => root.classList.remove("fx-cur"));
    addEventListener("pointerdown", () => ring.classList.add("down"), { passive: true });
    addEventListener("pointerup", () => ring.classList.remove("down"), { passive: true });
  }

  /* ---------- 4 Magnetische Knöpfe (PC) ---------- */
  if (FINE) {
    const SEL = ".btn,#zoomBtn,.scanbtn,#openFilter,#openFilter2,.totop,.kv-stamp";
    let cur = null, qx, qy;
    const release = el => { el.classList.remove("fx-m"); G.to(el, { x: 0, y: 0, duration: .9, ease: "elastic.out(1,0.32)", overwrite: true, onComplete: () => G.set(el, { clearProps: "x,y" }) }); };
    addEventListener("pointermove", e => {
      if (e.pointerType !== "mouse") return;
      const el = e.target.closest ? e.target.closest(SEL) : null;
      if (cur && cur !== el) { release(cur); cur = null; }
      if (!el) return;
      if (el !== cur) { cur = el; el.classList.add("fx-m"); qx = G.quickTo(el, "x", { duration: .45, ease: "power3" }); qy = G.quickTo(el, "y", { duration: .45, ease: "power3" }); }
      const r = el.getBoundingClientRect(), k = el.classList.contains("kv-stamp") ? .22 : .32;
      qx((e.clientX - (r.left + r.width / 2)) * k); qy((e.clientY - (r.top + r.height / 2)) * k);
    }, { passive: true });
    document.addEventListener("pointerleave", () => { if (cur) { release(cur); cur = null; } });
  }

  /* ---------- 5 Reveal + 6 Kinetic Typography ---------- */
  if (!ST) return;
  const REV = ".grid>.card,.panel,.tip,.witem,.wk,.cart,.receipt,.empty";
  const HEAD = ".meta h2,.sec-h,.panel>h2:first-child,.panel>h3:first-child,.wkbox h3";
  const typing = () => document.activeElement && document.activeElement.matches && document.activeElement.matches("input,textarea");
  function splitHead(h) {
    if (h.dataset.fx || h.children.length || !h.textContent.trim()) return null;
    h.dataset.fx = "1";
    const txt = h.textContent.trim();
    h.setAttribute("aria-label", txt);
    h.innerHTML = txt.split(/\s+/).map(w => `<span class="fxw" aria-hidden="true"><span>${w.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]))}</span></span>`).join(" ");
    return h;
  }
  let pend = false;
  function scan() {
    pend = false;
    ST.getAll().forEach(t => { if (t.trigger && !t.trigger.isConnected) t.kill(); }); // Auslöser entfernter Karten aufräumen
    const fresh = [...document.querySelectorAll(REV)].filter(el => !el.dataset.fx && !el.closest(".sheet"));
    fresh.forEach(el => el.dataset.fx = "1");
    const heads = [...document.querySelectorAll(HEAD)].filter(h => !h.closest(".sheet")).map(splitHead).filter(Boolean);
    if (typing()) { ST.refresh(); return; } // beim Tippen in der Suche nichts einfliegen lassen
    if (fresh.length) {
      G.set(fresh, { clipPath: "inset(22% 0% 0% 0% round 24px)", y: 46, rotateX: -10, transformPerspective: 1000, transformOrigin: "50% 0%", opacity: 0 });
      ST.batch(fresh, {
        start: "top 94%", once: true,
        onEnter: b => G.to(b, { clipPath: "inset(0% 0% 0% 0% round 24px)", y: 0, rotateX: 0, opacity: 1, duration: .95, ease: "expo.out", stagger: .07, overwrite: true,
          onComplete() { G.set(this.targets(), { clearProps: "clipPath,transform,opacity,transformPerspective,transformOrigin" }); } })
      });
    }
    heads.forEach(h => {
      const words = h.querySelectorAll(".fxw>span");
      G.fromTo(words, { yPercent: 115, rotate: 4 }, { yPercent: 0, rotate: 0, duration: 1, ease: "expo.out", stagger: .06,
        scrollTrigger: { trigger: h, start: "top 96%", once: true } });
      if (h.matches(".meta h2")) G.fromTo(h, { letterSpacing: "-0.015em" }, { letterSpacing: "-0.04em", ease: "none",
        scrollTrigger: { trigger: h, start: "top 85%", end: "top 15%", scrub: .6 } });
    });
    ST.refresh();
  }
  const mo = new MutationObserver(() => { if (!pend) { pend = true; requestAnimationFrame(scan); } });
  const go = () => { const m = document.querySelector("main"); if (m) mo.observe(m, { childList: true, subtree: true }); scan(); };
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", go) : go();
})();
