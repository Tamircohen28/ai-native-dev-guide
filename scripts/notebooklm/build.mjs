#!/usr/bin/env node
// Package the book for NotebookLM: one notebook, and one Video Overview, per section.
//
// Run it with `make notebookLM` (which runs `npm ci` first when node_modules is missing).
// The output, notebookLM/, is a build output like dist/: it is git-ignored and wiped and
// rebuilt on every run.
//
// Pipeline:
//   1. Read the reading order from the "## Contents" tables in book/README.md (the same
//      parser as scripts/pdf/build.mjs). Each part is a section; a "#### " sub-heading
//      inside a part (the Workshop) starts a section of its own. The appendices part is
//      left out: it is reference material, so every package links to it online instead.
//   2. For each section, write notebookLM/NN-<slug>/:
//        01-video-outline.md     narrative guidance built only from the chapters' own text:
//                                learning objectives (each opener), per chapter the core
//                                concept (Mental model), key sections, suggested visuals
//                                and key takeaways (Checklist), then narration guidance
//        NN-chNN-<slug>.md       each chapter, cleaned: no footer navigation, links to other
//                                book files made absolute GitHub URLs, images pointed at
//                                media/*.png, a "Diagram: media/…png — caption" line after
//                                every Mermaid block (the block itself is kept as text)
//        visual-references.pdf   every figure and diagram in the section, one per page,
//                                with a caption (puppeteer page.pdf)
//        media/*.png             the section's SVG figures and Mermaid diagrams as PNG at
//                                2x on white (NotebookLM does not accept SVG sources)
//        README.md               what to upload, source count against the notebook limit,
//                                Video Overview settings and a steering prompt
//   3. Write notebookLM/README.md: an overview of the sections.
//
// It fails (exit 1) on a Mermaid block that does not render, a referenced image that does
// not exist, or a section without chapters. The Markdown output is deterministic for a
// given commit; BOOK_COMMIT and BOOK_VERSION override the build identity, as for make pdf.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import puppeteer from "puppeteer";
import { renderMermaid } from "@mermaid-js/mermaid-cli";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const bookDir = path.join(root, "book");
const outDir = path.join(root, "notebookLM");

const BOOK = {
  title: "AI-Native Development: Zero to Hero",
  author: "Tamir Cohen",
  repo: "https://github.com/Tamircohen28/ai-native-dev-guide",
};
const BLOB = `${BOOK.repo}/blob/main/`;

// NotebookLM facts, as read in Google's official help on this date. Update both together.
const LIMITS = {
  checked: "2026-11-26",
  typesUrl: "https://support.google.com/notebooklm/answer/16215270",
  plansUrl: "https://support.google.com/notebooklm/answer/16213268",
  faqUrl: "https://support.google.com/notebooklm/answer/16269187",
  videoUrl: "https://support.google.com/notebooklm/answer/16454555",
  free: 50,
};

// The chapter skeleton's standard headings: not listed as a chapter's key sections.
const SKELETON = new Set(["Mental model", "From the field", "Common problems", "Checklist", "Try it", "Sources"]);

const log = (msg) => console.log(`notebooklm: ${msg}`);
const fail = (msg) => {
  console.error(`notebooklm: ERROR: ${msg}`);
  process.exit(1);
};

// --- Build identity (commit and version only: no clock) ------------------------------

function git(...args) {
  try {
    return execFileSync("git", args, { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return "";
  }
}

function buildIdentity() {
  const commit = process.env.BOOK_COMMIT || git("rev-parse", "HEAD") || "unknown";
  const short = commit === "unknown" ? "unknown" : commit.slice(0, 7);
  let version = process.env.BOOK_VERSION;
  if (!version) {
    const changelog = fs.readFileSync(path.join(root, "docs", "CHANGELOG.md"), "utf8");
    const m = changelog.match(/^## \[(\d+\.\d+\.\d+)\]/m);
    const released = m ? m[1] : "0.0.0";
    const atTag = git("tag", "--points-at", "HEAD").split("\n").includes(`v${released}`);
    version = atTag ? released : `${released}+${short}`;
  }
  return { commit, short, version };
}

// --- Reading order ------------------------------------------------------------------

// [{ label, groups: [{ label, files: [{ num, file }] }] }], as in scripts/pdf/build.mjs.
function readingOrder() {
  const readme = fs.readFileSync(path.join(bookDir, "README.md"), "utf8").split("\n");
  const start = readme.findIndex((l) => l.trim() === "## Contents");
  if (start < 0) fail("book/README.md has no '## Contents' section");
  const parts = [];
  for (let i = start + 1; i < readme.length; i++) {
    const line = readme[i];
    if (/^## /.test(line)) break;
    let m;
    if ((m = line.match(/^### (.+)$/))) {
      parts.push({ label: m[1].trim(), groups: [{ label: null, files: [] }] });
    } else if ((m = line.match(/^#### (.+)$/))) {
      if (!parts.length) fail(`sub-heading before any part heading: ${line}`);
      parts.at(-1).groups.push({ label: m[1].trim(), files: [] });
    } else if ((m = line.match(/^\|\s*([^|]*?)\s*\|\s*\[[^\]]+\]\(([^)#]+\.md)\)/))) {
      if (!parts.length) fail(`contents row before any part heading: ${line}`);
      parts.at(-1).groups.at(-1).files.push({ num: m[1], file: m[2] });
    }
  }
  for (const p of parts)
    for (const g of p.groups)
      for (const f of g.files) if (!fs.existsSync(path.join(bookDir, f.file))) fail(`Contents lists a missing file: book/${f.file}`);
  return parts;
}

const slugify = (s) =>
  s
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .trim()
    .replace(/[\s-]+/g, "-");

// Sections: every part's unlabelled group, plus each labelled sub-group, in order.
function sections(parts) {
  const out = [];
  for (const p of parts) {
    if (/^appendi/i.test(p.label)) continue;
    const partTitle = p.label.replace(/^Part\s+[IVXLC]+\s*[—–-]\s*/i, "").trim();
    for (const g of p.groups) {
      if (!g.label && g.files.length === 0 && p.groups.length > 1) continue; // part holds only sub-groups
      const title = g.label ? g.label.trim() : partTitle;
      out.push({ part: p.label, title, files: g.files.map((f) => f.file) });
    }
  }
  out.forEach((s, i) => {
    s.dir = `${String(i + 1).padStart(2, "0")}-${slugify(s.title)}`;
    if (s.files.length === 0) fail(`section "${s.title}" (${s.part}) has no chapters`);
  });
  if (out.length === 0) fail("no sections found in book/README.md");
  return out;
}

function appendices(parts) {
  return parts
    .filter((p) => /^appendi/i.test(p.label))
    .flatMap((p) => p.groups.flatMap((g) => g.files))
    .map((f) => {
      const h1 = fs.readFileSync(path.join(bookDir, f.file), "utf8").match(/^# (.+)$/m);
      return { file: f.file, title: h1 ? h1[1].replace(/`/g, "").trim() : f.file };
    });
}

// --- Markdown helpers ---------------------------------------------------------------

// Mark each line as inside or outside a fenced code block (CommonMark fence rules).
function fenceMap(lines) {
  let open = null;
  return lines.map((line) => {
    const m = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (!open) {
      if (m) {
        open = { ch: m[1][0], len: m[1].length, info: m[2].trim() };
        return { fence: "open", info: open.info };
      }
      return { fence: null };
    }
    if (m && m[1][0] === open.ch && m[1].length >= open.len && m[2].trim() === "") {
      const info = open.info;
      open = null;
      return { fence: "close", info };
    }
    return { fence: "in", info: open.info };
  });
}

// Apply fn to the parts of a line outside inline code spans.
function outsideCode(line, fn) {
  return line
    .split(/(`+[^`]*?`+)/)
    .map((seg, i) => (i % 2 ? seg : fn(seg)))
    .join("");
}

const plain = (s) =>
  s
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[((?:[^\[\]]|\[[^\]]*\])*)\]\([^)]*\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();

function stripFooter(text) {
  const lines = text.replace(/\s+$/, "").split("\n");
  if (lines.length && lines.at(-1).includes("[Contents](README.md)")) {
    lines.pop();
    while (lines.length && lines.at(-1).trim() === "") lines.pop();
    if (lines.length && lines.at(-1).trim() === "---") lines.pop();
  }
  return lines.join("\n") + "\n";
}

const diagramKind = (src) => {
  const first = src.split("\n").find((l) => l.trim() && !l.trim().startsWith("%%")) || "";
  const w = first.trim().split(/\s+/)[0];
  const names = {
    sequenceDiagram: "sequence diagram",
    flowchart: "flowchart",
    graph: "flowchart",
    stateDiagram: "state diagram",
    "stateDiagram-v2": "state diagram",
    classDiagram: "class diagram",
    erDiagram: "entity-relationship diagram",
    gantt: "Gantt chart",
    pie: "pie chart",
    timeline: "timeline",
    mindmap: "mind map",
    journey: "user journey",
    quadrantChart: "quadrant chart",
    gitGraph: "git graph",
  };
  return names[w] || "diagram";
};

// Parse one chapter into the parts the package needs.
function parseChapter(file) {
  const text = stripFooter(fs.readFileSync(path.join(bookDir, file), "utf8"));
  const lines = text.split("\n");
  const fm = fenceMap(lines);
  const h1 = text.match(/^# (.+)$/m);
  if (!h1) fail(`book/${file} has no '# ' title`);
  const hm = h1[1].match(/^(\d+)\s*[—–-]\s*(.+)$/);
  const num = hm ? Number(hm[1]) : Number(file.split("-")[0]);
  const title = (hm ? hm[2] : h1[1]).replace(/`/g, "").trim();
  const nn = String(num).padStart(2, "0");

  const headings = [];
  const figures = [];
  const diagrams = [];
  let heading = title;
  let block = null;
  const sectionText = new Map();
  let current = null;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const f = fm[i];
    if (f.fence === "open" && f.info === "mermaid") block = { start: i, src: [] };
    else if (f.fence === "in" && block) block.src.push(line);
    else if (f.fence === "close" && block) {
      const k = diagrams.length + 1;
      diagrams.push({
        end: i,
        k,
        source: block.src.join("\n"),
        kind: diagramKind(block.src.join("\n")),
        heading,
        png: `ch${nn}-diagram-${k}.png`,
      });
      block = null;
    }
    if (f.fence !== null) {
      if (current) sectionText.get(current).push(line);
      continue;
    }
    let m;
    if ((m = line.match(/^(#{2,3}) (.+)$/))) {
      heading = plain(m[2]).replace(/`/g, "");
      if (m[1] === "##") {
        current = heading;
        sectionText.set(current, []);
        if (!SKELETON.has(heading)) headings.push(m[2].trim());
      } else if (current) sectionText.get(current).push(line);
      continue;
    }
    if (current) sectionText.get(current).push(line);
    const code = line.replace(/`[^`]*`/g, "");
    for (const im of code.matchAll(/!\[([^\]]*)\]\(([^)\s]+)\)/g)) {
      const src = im[2];
      if (/^[a-z]+:/i.test(src)) continue;
      const abs = path.resolve(bookDir, src);
      if (!fs.existsSync(abs)) fail(`book/${file}: image not found: ${src}`);
      if (!/\.(svg|png|jpe?g)$/i.test(src)) fail(`book/${file}: unsupported image type: ${src}`);
      figures.push({ src: abs, alt: plain(im[1]), png: path.basename(src).replace(/\.[^.]+$/, ".png") });
    }
  }

  // Opener: the first paragraph after the title.
  const h1i = lines.findIndex((l) => /^# /.test(l));
  const para = [];
  for (let i = h1i + 1; i < lines.length; i++) {
    if (!lines[i].trim()) {
      if (para.length) break;
      continue;
    }
    if (/^#/.test(lines[i])) break;
    para.push(lines[i]);
  }
  const opener = plain(para.join(" "));

  // Mental model: the first prose paragraph, trimmed to at most three sentences.
  const mm = sectionText.get("Mental model") || [];
  const mp = [];
  for (const l of mm) {
    if (!l.trim()) {
      if (mp.length) break;
      continue;
    }
    if (/^\s*(```|~~~|!\[|\||>)/.test(l)) {
      if (mp.length) break;
      continue;
    }
    mp.push(l);
  }
  const sentences = plain(mp.join(" ")).split(/(?<=[.!?:]["”]?)\s+(?=[A-Z"“*`(])/);
  const concept = [];
  let words = 0;
  for (const s of sentences) {
    if (concept.length >= 3 || (concept.length && words >= 45)) break;
    concept.push(s);
    words += s.split(/\s+/).length;
  }

  // Checklist items, rewritten from first person to statements about the reader.
  const checklist = (sectionText.get("Checklist") || [])
    .map((l) => l.match(/^\s*[-*]\s+\[[ xX]\]\s+(.*)$/))
    .filter(Boolean)
    .map((m) => statement(plain(m[1])));

  return { file, num, nn, title, opener, concept: concept.join(" "), headings, figures, diagrams, checklist, text, lines, fm };
}

function statement(s) {
  return s
    .replace(/^I am\b/, "You are")
    .replace(/^I'm\b/, "You're")
    .replace(/^I've\b/, "You've")
    .replace(/^I\b/, "You")
    .replace(/^My\b/, "Your")
    .replace(/\bI am\b/g, "you are")
    .replace(/\bI'm\b/g, "you're")
    .replace(/\bI've\b/g, "you've")
    .replace(/\bI\b/g, "you")
    .replace(/\bmy\b/g, "your")
    .replace(/\bMy\b/g, "Your")
    .replace(/\bme\b/g, "you")
    .replace(/\bmyself\b/g, "yourself");
}

// --- Cleaned chapter ----------------------------------------------------------------

function cleanChapter(ch) {
  const byEnd = new Map(ch.diagrams.map((d) => [d.end, d]));
  const out = [];
  ch.lines.forEach((line, i) => {
    const f = ch.fm[i];
    if (f.fence === null) {
      line = outsideCode(line, (seg) =>
        seg
          .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (all, alt, src) =>
            /^[a-z]+:/i.test(src) ? all : `![${alt}](media/${path.basename(src).replace(/\.[^.]+$/, ".png")})`,
          )
          .replace(/\]\((?![a-z][a-z0-9+.-]*:|#|media\/)([^)\s]+)\)/gi, (_, href) => `](${absolute(href)})`)
          .replace(/^(\s*\[[^\]]+\]:\s*)(?![a-z][a-z0-9+.-]*:|#)(\S+)/i, (_, pre, href) => pre + absolute(href)),
      );
    }
    out.push(line);
    const d = byEnd.get(i);
    if (d) out.push("", `Diagram: media/${d.png} — ${caption(ch, d)}`);
  });
  return out.join("\n").replace(/\s+$/, "") + "\n";
}

function absolute(href) {
  const [target, hash] = href.split("#");
  const rel = path.posix.normalize(path.posix.join("book", target));
  if (rel.startsWith("..")) fail(`link leaves the repository: ${href}`);
  return BLOB + rel + (hash ? `#${hash}` : "");
}

const caption = (ch, d) => `${d.heading} (${d.kind})`;

// --- Rendering ----------------------------------------------------------------------

const MERMAID_CONFIG = {
  theme: "neutral",
  fontFamily: '"Helvetica Neue", Helvetica, Arial, "Liberation Sans", "DejaVu Sans", sans-serif',
  flowchart: { useMaxWidth: true },
  sequence: { useMaxWidth: true },
};

async function pool(items, n, fn) {
  const queue = [...items];
  await Promise.all(Array.from({ length: n }, async () => {
    while (queue.length) await fn(queue.shift());
  }));
}

async function renderDiagrams(browser, chapters) {
  const all = chapters.flatMap((ch) => ch.diagrams.map((d) => ({ ch, d })));
  const failures = [];
  await pool(all, 4, async ({ ch, d }) => {
    try {
      const { data } = await renderMermaid(browser, d.source, "png", {
        backgroundColor: "white",
        mermaidConfig: MERMAID_CONFIG,
        viewport: { width: 1400, height: 900, deviceScaleFactor: 2 },
      });
      d.data = Buffer.from(data);
    } catch (err) {
      failures.push(`book/${ch.file} mermaid block ${d.k}: ${String(err.message || err).split("\n")[0]}`);
    }
  });
  if (failures.length) fail(`${failures.length} Mermaid block(s) failed to render:\n  ${failures.join("\n  ")}`);
  return all.length;
}

// Rasterise SVG figures at 2x on white; each figure renders once and is copied per section.
async function renderFigures(browser, chapters) {
  const unique = [...new Set(chapters.flatMap((ch) => ch.figures.map((f) => f.src)))].sort();
  const cache = new Map();
  const page = await browser.newPage();
  for (const src of unique) {
    if (!/\.svg$/i.test(src)) {
      cache.set(src, fs.readFileSync(src));
      continue;
    }
    await page.setViewport({ width: 1600, height: 1200, deviceScaleFactor: 2 });
    // A file:// page, so the file:// image is same-origin and loads.
    const tmp = path.join(outDir, ".figure.html");
    fs.writeFileSync(
      tmp,
      `<!doctype html><html><head><style>html,body{margin:0;background:#fff}img{display:block}</style></head><body><img id="f" src="${pathToFileURL(src).href}"></body></html>`,
    );
    await page.goto(pathToFileURL(tmp).href, { waitUntil: "load" });
    fs.rmSync(tmp);
    const size = await page.$eval("#f", (img) => ({ w: img.naturalWidth, h: img.naturalHeight }));
    if (!size.w || !size.h) fail(`could not load figure: ${path.relative(root, src)}`);
    // Small figures are drawn larger, so every PNG is at least ~1600 px wide at 2x.
    const scale = Math.max(1, Math.min(2, 800 / size.w));
    const w = Math.round(size.w * scale);
    const h = Math.round(size.h * scale);
    await page.$eval("#f", (img, { w, h }) => Object.assign(img.style, { width: `${w}px`, height: `${h}px` }), { w, h });
    await page.setViewport({ width: w, height: h, deviceScaleFactor: 2 });
    cache.set(src, Buffer.from(await page.screenshot({ type: "png", clip: { x: 0, y: 0, width: w, height: h }, omitBackground: false })));
  }
  await page.close();
  return cache;
}

const escapeHtml = (s) =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

async function writePdf(browser, sec, visuals, dest) {
  const pages = visuals.map(
    (v) => `<section class="page"><p class="cap"><b>Chapter ${v.ch.num}: ${escapeHtml(v.ch.title)}</b><br>${escapeHtml(v.label)}</p>
<div class="img"><img src="${pathToFileURL(v.file).href}" alt="${escapeHtml(v.label)}"></div>
<p class="file">media/${escapeHtml(v.png)}</p></section>`,
  );
  const title = `${sec.title} — visual references`;
  const intro = `<section class="page intro"><h1>${escapeHtml(sec.title)}</h1><p class="sub">Visual references for ${escapeHtml(BOOK.title)}</p>
<ol>${visuals.map((v) => `<li>Chapter ${v.ch.num}: ${escapeHtml(v.label)}</li>`).join("")}</ol></section>`;
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title>
<style>
@page { size: A4 landscape; margin: 12mm; }
html, body { margin: 0; background: #fff; color: #1a1a1a; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
.page { height: 185mm; display: flex; flex-direction: column; page-break-after: always; break-after: page; overflow: hidden; }
.page:last-child { page-break-after: auto; break-after: auto; }
.cap { margin: 0 0 4mm; font-size: 13pt; line-height: 1.35; }
.img { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }
.img img { max-width: 100%; max-height: 100%; object-fit: contain; }
.file { margin: 3mm 0 0; font-size: 9pt; color: #666; }
.intro h1 { font-size: 26pt; margin: 20mm 0 2mm; }
.intro .sub { font-size: 13pt; color: #444; margin: 0 0 8mm; }
.intro ol { font-size: 10.5pt; line-height: 1.45; columns: 2; column-gap: 14mm; padding-left: 2.2em; }
.intro li { break-inside: avoid; padding-left: 0.3em; }
</style></head><body>${intro}${pages.join("\n")}</body></html>`;
  const page = await browser.newPage();
  const tmp = path.join(outDir, `.${sec.dir}.html`);
  fs.writeFileSync(tmp, html);
  await page.goto(pathToFileURL(tmp).href, { waitUntil: "load" });
  await page.pdf({ path: dest, preferCSSPageSize: true, printBackground: true });
  await page.close();
  fs.rmSync(tmp);
  return visuals.length + 1;
}

// --- Writers ------------------------------------------------------------------------

const words = (s) => s.split(/\s+/).filter(Boolean).length;

function audience() {
  const readme = fs.readFileSync(path.join(bookDir, "README.md"), "utf8").replace(/\*/g, "");
  const m = readme.match(/for (developers who [^.]+)\./);
  return m ? `For ${m[1]}.` : "For developers who build software with coding agents.";
}

function outlineMd(sec, chapters, aud) {
  const o = [`# ${sec.title}: video outline`, "", `Audience: ${aud.replace(/^For /, "")}`, ""];
  o.push(`This section of *${BOOK.title}* covers chapters ${chapters[0].num} to ${chapters.at(-1).num}. Each chapter below is a scene group; follow them in order.`, "");
  o.push("## Learning objectives", "");
  for (const ch of chapters) {
    const goal = ch.opener.replace(/^After this chapter you (can|have) /, (_, v) => (v === "have" ? "Have " : ""));
    o.push(`- **Chapter ${ch.num}, ${ch.title}:** ${goal.charAt(0).toUpperCase()}${goal.slice(1)}`);
  }
  o.push("");
  for (const ch of chapters) {
    o.push(`## Chapter ${ch.num}: ${ch.title}`, "");
    o.push(`Source file: \`${chapterFileName(sec, chapters, ch)}\``, "");
    o.push("**Core concept**", "", ch.concept || "(This chapter has no Mental model paragraph.)", "");
    o.push("**Key sections**", "");
    for (const h of ch.headings) o.push(`- ${h}`);
    if (!ch.headings.length) o.push("- (Only the standard chapter sections.)");
    o.push("", "**Suggested visuals**", "");
    const vis = visualsOf(ch);
    for (const v of vis) o.push(`- \`media/${v.png}\`: ${v.label}`);
    if (!vis.length) o.push("- (No figures or diagrams in this chapter.)");
    o.push("", "**Key takeaways**", "");
    for (const t of ch.checklist.slice(0, 5)) o.push(`- ${t}`);
    if (!ch.checklist.length) o.push("- (This chapter has no checklist.)");
    o.push("");
  }
  o.push("## Narration guidance", "");
  o.push("- Use an explainer tone: plain words, one idea at a time, for a developer audience.");
  o.push("- Follow the chapter order above; each chapter builds on the one before it.");
  o.push("- Show the diagrams named under Suggested visuals; they are in `visual-references.pdf` in the same order.");
  o.push("- Define each term the first time it is used.");
  o.push("- Use only facts from the chapter sources. Do not invent version numbers, prices, dates or statistics; where a chapter dates a fact (\"as of Nov 2026\"), say so.");
  return o.join("\n") + "\n";
}

function visualsOf(ch) {
  const v = [];
  const seen = new Set();
  for (const f of ch.figures) {
    if (seen.has(f.png)) continue;
    seen.add(f.png);
    v.push({ ch, png: f.png, label: /^Chart:/.test(f.alt) ? f.alt : `Figure: ${f.alt}`, kind: "figure" });
  }
  for (const d of ch.diagrams) v.push({ ch, png: d.png, label: `Diagram ${d.k}: ${caption(ch, d)}`, kind: "diagram" });
  return v;
}

function chapterFileName(sec, chapters, ch) {
  const i = chapters.indexOf(ch);
  const slug = ch.file.replace(/\.md$/, "").replace(/^\d+-/, "");
  return `${String(i + 2).padStart(2, "0")}-ch${ch.nn}-${slug}.md`;
}

function sectionReadme(sec, chapters, stats, id, apps) {
  const r = [`# ${sec.title}: NotebookLM package`, ""];
  r.push(`Sources for one NotebookLM notebook and one Video Overview covering chapters ${chapters[0].num} to ${chapters.at(-1).num} of *${BOOK.title}* by ${BOOK.author}. This README is not a source: do not upload it.`, "");
  r.push(`Generated by \`make notebookLM\` from commit \`${id.short}\` (version ${id.version}). Do not edit by hand; change the book and regenerate.`, "");
  r.push("## Contents", "", "| File | What it is | Upload |", "|---|---|---|");
  r.push("| `01-video-outline.md` | Narrative guidance: learning objectives, per-chapter concept, sections, visuals, takeaways | Yes |");
  for (const ch of chapters) r.push(`| \`${chapterFileName(sec, chapters, ch)}\` | Chapter ${ch.num}: ${ch.title} | Yes |`);
  r.push(`| \`visual-references.pdf\` | Every figure and diagram in the section with a caption, ${stats.pages} pages | Yes |`);
  r.push(`| \`media/\` | ${stats.pngs} PNG images: the figures and Mermaid diagrams at 2x | Optional |`);
  r.push("| `README.md` | This file | No |", "");
  const figs = chapters.flatMap((ch) => ch.figures.map((f) => f.png)).filter((p, i, a) => a.indexOf(p) === i && p.startsWith("fig-"));
  r.push("## What to upload", "");
  r.push(`Upload the ${stats.sources} required sources: every \`*.md\` file except this README, and \`visual-references.pdf\`.`);
  if (figs.length) r.push(`If you have room, also upload the concept figures as images: ${figs.map((f) => `\`media/${f}\``).join(", ")}.`);
  r.push("");
  r.push(`That is ${stats.sources} sources (${stats.sources + stats.pngs} with every PNG). As read on ${LIMITS.checked}, Google's help lists ${LIMITS.free} sources per notebook on the free plan and more on paid plans, with each source up to 500,000 words or 200 MB; the limits are marked as subject to change, so check the current limit for your plan:`, "");
  r.push(`- Plans and per-notebook source limits: ${LIMITS.plansUrl}`);
  r.push(`- Per-source size limits: ${LIMITS.faqUrl}`);
  r.push(`- Supported source types (Markdown, PDF and PNG are listed; SVG is not): ${LIMITS.typesUrl}`, "");
  r.push("## Video Overview settings", "");
  r.push(`From the notebook's Studio panel, create a Video Overview (help: ${LIMITS.videoUrl}).`, "");
  r.push("1. Format: **Explainer** for a structured walk-through, or **Cinematic** for a richer one (Google lists Cinematic as English-only and for users 18 and over).");
  r.push("2. Turn on **Review producer notes**.");
  r.push("3. Paste the steering prompt below.");
  r.push("4. Review the proposed narrative and scenes against `01-video-outline.md` before you proceed: after you proceed, the producer notes cannot be refined further.", "");
  r.push("### Steering prompt", "", "```text");
  r.push(`Explain "${sec.title}" from the book ${BOOK.title} to developers, following 01-video-outline.md.`);
  r.push(`Cover the chapters in order: ${chapters.map((c) => `${c.num} ${c.title}`).join("; ")}.`);
  r.push("For each chapter, state the core concept, walk through the key sections, show the diagrams listed under Suggested visuals (they are in visual-references.pdf), and end with the key takeaways.");
  r.push("Define terms on first use. Use only facts from the sources; do not invent version numbers, prices or statistics.");
  r.push("```", "");
  r.push("## Appendices (online, not included)", "");
  r.push("The appendices are reference material that narrates poorly, so they are not sources here. Read them on GitHub:", "");
  for (const a of apps) r.push(`- [${a.title}](${BLOB}book/${a.file})`);
  return r.join("\n") + "\n";
}

function rootReadme(rows, id, apps) {
  const r = ["# NotebookLM packages", ""];
  r.push(`*${BOOK.title}* by ${BOOK.author}, packaged as one NotebookLM notebook, and one Video Overview, per section. Each folder holds the sources to upload for that notebook; its README says which files and how to set up the video.`, "");
  r.push(`Generated by \`make notebookLM\` from commit \`${id.short}\` (version ${id.version}). This folder is a build output: it is git-ignored, and every run wipes and rebuilds it.`, "");
  r.push("| Section | Chapters | Source files | Images | Words |", "|---|---|---|---|---|");
  for (const x of rows) r.push(`| ${x.title} (\`${x.dir}/\`) | ${x.chapters} | ${x.sources} | ${x.pngs} | ${x.words.toLocaleString("en-US")} |`);
  r.push("", "Source files are the Markdown files to upload plus `visual-references.pdf`; images are the PNGs in `media/`; words count the Markdown sources.", "");
  r.push("## Regenerate", "", "```bash", "make notebookLM", "```", "");
  r.push("It needs Node.js 22.12 or later and runs `npm ci` on first use. See `docs/user/reference/commands.md`.", "");
  r.push("## Why the appendices are excluded", "");
  r.push("The appendices (cheat sheet, glossary, templates, sources, learning path) are reference tables and lists: they make poor narration and would crowd the chapters out of a video. Every package links to them online instead:", "");
  for (const a of apps) r.push(`- [${a.title}](${BLOB}book/${a.file})`);
  return r.join("\n") + "\n";
}

// --- Main ---------------------------------------------------------------------------

async function main() {
  const id = buildIdentity();
  log(`version ${id.version}, commit ${id.short}`);
  const parts = readingOrder();
  const secs = sections(parts);
  const apps = appendices(parts);
  const aud = audience();
  for (const s of secs) s.chapters = s.files.map(parseChapter);
  const allChapters = secs.flatMap((s) => s.chapters);

  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  const launchArgs = process.env.CI ? ["--no-sandbox", "--disable-setuid-sandbox"] : [];
  const browser = await puppeteer.launch({ headless: true, args: [...launchArgs, "--allow-file-access-from-files"] });
  const rows = [];
  try {
    const nDiagrams = await renderDiagrams(browser, allChapters);
    const figures = await renderFigures(browser, allChapters);
    log(`${allChapters.length} chapters in ${secs.length} sections, ${nDiagrams} diagrams, ${figures.size} figures rendered`);

    for (const sec of secs) {
      const dir = path.join(outDir, sec.dir);
      const media = path.join(dir, "media");
      fs.mkdirSync(media, { recursive: true });
      const chapters = sec.chapters;
      const visuals = chapters.flatMap(visualsOf);
      for (const ch of chapters) {
        for (const f of ch.figures) fs.writeFileSync(path.join(media, f.png), figures.get(f.src));
        for (const d of ch.diagrams) fs.writeFileSync(path.join(media, d.png), d.data);
      }
      for (const v of visuals) v.file = path.join(media, v.png);

      let wordCount = 0;
      const outline = outlineMd(sec, chapters, aud);
      fs.writeFileSync(path.join(dir, "01-video-outline.md"), outline);
      wordCount += words(outline);
      for (const ch of chapters) {
        const md = cleanChapter(ch);
        fs.writeFileSync(path.join(dir, chapterFileName(sec, chapters, ch)), md);
        wordCount += words(md);
      }
      const pages = await writePdf(browser, sec, visuals, path.join(dir, "visual-references.pdf"));
      const pngs = fs.readdirSync(media).filter((f) => f.endsWith(".png")).length;
      const stats = { pages, pngs, sources: chapters.length + 2 };
      fs.writeFileSync(path.join(dir, "README.md"), sectionReadme(sec, chapters, stats, id, apps));
      rows.push({ title: sec.title, dir: sec.dir, chapters: chapters.map((c) => c.num).join(", "), sources: stats.sources, pngs, words: wordCount });
      log(`${sec.dir}: ${chapters.length} chapters, ${stats.sources} sources, ${pngs} PNGs, ${pages} PDF pages, ${wordCount} words`);
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(outDir, "README.md"), rootReadme(rows, id, apps));
  log(`wrote ${path.relative(root, outDir)}/ (${rows.length} sections)`);
}

main().catch((err) => fail(err.stack || String(err)));
