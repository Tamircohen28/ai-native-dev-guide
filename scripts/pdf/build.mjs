#!/usr/bin/env node
// Build the whole book as one PDF: dist/AI-Native Development.pdf
//
// Run it with `make pdf` (which runs `npm ci` first when node_modules is missing).
//
// Pipeline:
//   1. Read the reading order from the "## Contents" tables in book/README.md.
//   2. Render each Markdown file to HTML with markdown-it. The footer navigation line is
//      dropped and links between chapters become in-document anchors. The appendices are
//      not printed: the contents lists them as links to their files on GitHub, and every
//      link to an appendix points there. In each chapter, external links get numbered
//      citation markers and "## Sources" becomes the matching numbered reference list.
//   3. Render every ```mermaid block to inline SVG with @mermaid-js/mermaid-cli. A block
//      that fails to render fails the build.
//   4. Paginate with Paged.js inside headless Chromium (puppeteer) and print to PDF:
//      cover, table of contents with page numbers, page numbers centred at the bottom.
//   5. Write the PDF metadata with pypdf (scripts/pdf/metadata.py).
//
// Build identity comes from git and the clock. Override it for reproducible builds with
// BOOK_COMMIT (full SHA), BOOK_VERSION, BOOK_BUILD_TIME (ISO 8601 UTC) or SOURCE_DATE_EPOCH.
// BOOK_PDF_KEEP_HTML=1 keeps dist/pdf-build/book.html for debugging.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import MarkdownIt from "markdown-it";
import puppeteer from "puppeteer";
import { renderMermaid } from "@mermaid-js/mermaid-cli";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const bookDir = path.join(root, "book");
const distDir = path.join(root, "dist");
const workDir = path.join(distDir, "pdf-build");

export const BOOK = {
  title: "AI-Native Development",
  subtitle: "Zero to Hero — a field guide to building software with coding agents",
  author: "Tamir Cohen",
  repo: "https://github.com/Tamircohen28/ai-native-dev-guide",
  license: "CC BY-NC-SA 4.0",
  licenseUrl: "https://creativecommons.org/licenses/by-nc-sa/4.0/",
  keywords:
    "AI-native development, coding agents, Claude Code, agentic coding, MCP, subagents, skills, hooks, prompt engineering",
};
const OUT_PDF = path.join(distDir, `${BOOK.title}.pdf`);

const log = (msg) => console.log(`pdf: ${msg}`);
const fail = (msg) => {
  console.error(`pdf: ERROR: ${msg}`);
  process.exit(1);
};

// --- Build identity -----------------------------------------------------------------

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
    // Exactly at the release tag: the plain version. Anywhere else: version+short SHA.
    const atTag = git("tag", "--points-at", "HEAD").split("\n").includes(`v${released}`);
    version = atTag ? released : `${released}+${short}`;
  }
  let built;
  if (process.env.BOOK_BUILD_TIME) built = new Date(process.env.BOOK_BUILD_TIME);
  else if (process.env.SOURCE_DATE_EPOCH) built = new Date(Number(process.env.SOURCE_DATE_EPOCH) * 1000);
  else built = new Date();
  if (Number.isNaN(built.getTime())) fail("BOOK_BUILD_TIME / SOURCE_DATE_EPOCH is not a valid date");
  const timestamp = built.toISOString().replace(/\.\d{3}Z$/, "Z");
  return { commit, short, version, timestamp };
}

// --- Reading order ------------------------------------------------------------------

// Returns [{ label, sub: [{ label, files: [{num, file}] }] }]: parts, each with one or
// more groups (the Workshop sub-heading is a group with a label).
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
      parts.at(-1).groups.push({ label: m[1].trim(), files: [] });
    } else if ((m = line.match(/^\|\s*([^|]*?)\s*\|\s*\[[^\]]+\]\(([^)#]+\.md)\)/))) {
      if (!parts.length) fail(`contents row before any part heading: ${line}`);
      parts.at(-1).groups.at(-1).files.push({ num: m[1], file: m[2] });
    }
  }
  const all = parts.flatMap((p) => p.groups.flatMap((g) => g.files.map((f) => f.file)));
  if (all.length === 0) fail("no chapters found in the Contents tables of book/README.md");
  for (const f of all) if (!fs.existsSync(path.join(bookDir, f))) fail(`Contents lists a missing file: book/${f}`);
  return parts;
}

// --- Markdown -----------------------------------------------------------------------

const fileId = (file) => (file === "README.md" ? "about" : `ch-${file.replace(/\.md$/, "").split("-")[0]}`);

// GitHub's heading-anchor algorithm, so `chapter.md#some-heading` links keep working.
function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}\s_-]/gu, "")
    .replace(/\s/g, "-");
}

const escapeHtml = (s) =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function makeRenderer(knownFiles, mermaidBlocks) {
  // linkify turns a bare http(s) URL in prose into a link, so it can be cited like any
  // other; fuzzy matching stays off so "example.com" in prose is left alone.
  const md = new MarkdownIt({ html: false, linkify: true, typographer: false });
  md.linkify.set({ fuzzyLink: false, fuzzyEmail: false, fuzzyIP: false });
  md.core.ruler.after("linkify", "short-bare-urls", (state) => {
    for (const blk of state.tokens) {
      if (blk.type !== "inline" || !blk.children) continue;
      blk.children.forEach((t, i) => {
        const next = blk.children[i + 1];
        if (t.type === "link_open" && t.markup === "linkify" && next && next.type === "text") {
          next.content = next.content.replace(/^https?:\/\//, "");
        }
      });
    }
  });
  const blobBase = `${BOOK.repo}/blob/main/`;

  const resolveHref = (href, env) => {
    if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return href; // http:, https:, mailto:
    if (href.startsWith("#")) return `#${env.id}--${href.slice(1)}`;
    const [target, hash] = href.split("#");
    const rel = path.posix.normalize(path.posix.join("book", target));
    if (rel.startsWith("book/") && !rel.slice(5).includes("/") && knownFiles.has(rel.slice(5))) {
      const id = rel === "book/README.md" ? "toc" : fileId(rel.slice(5));
      return hash ? `#${fileId(rel.slice(5))}--${hash}` : `#${id}`;
    }
    // Anything else in the repo (LICENSE, a figure opened as a link): link to GitHub.
    return blobBase + rel + (hash ? `#${hash}` : "");
  };

  // External links in a chapter's body get a citation marker after the link text: [n],
  // numbered per chapter in order of first appearance (env.cite, see citeNumber). Links
  // into this repo (including the online appendices) are marked "online" instead.
  md.renderer.rules.link_open = (tokens, idx, opts, env, self) => {
    const t = tokens[idx];
    const href = resolveHref(t.attrGet("href"), env);
    t.attrSet("href", href);
    let kind = null;
    if (href.startsWith(BOOK.repo)) {
      kind = "online";
      t.attrJoin("class", "online");
    } else if (/^https?:/i.test(href) && env.cite) {
      kind = "cite";
    }
    (env.linkStack ||= []).push({ href, kind });
    return self.renderToken(tokens, idx, opts);
  };
  md.renderer.rules.link_close = (tokens, idx, opts, env, self) => {
    const open = (env.linkStack || []).pop();
    let html = self.renderToken(tokens, idx, opts);
    if (open && open.kind === "cite") {
      const n = citeNumber(env.cite, open.href, null);
      html += `<sup class="cite"><a href="${escapeHtml(open.href)}">[${n}]</a></sup>`;
    }
    return html;
  };

  md.renderer.rules.image = (tokens, idx, opts, env, self) => {
    const t = tokens[idx];
    const src = t.attrGet("src");
    const alt = self.renderInlineAsText(t.children, opts, env);
    const abs = path.resolve(bookDir, src);
    if (!/^[a-z]+:/i.test(src) && !fs.existsSync(abs)) fail(`${env.file}: image not found: ${src}`);
    const url = /^[a-z]+:/i.test(src) ? src : pathToFileURL(abs).href;
    return `<figure class="figure"><img src="${escapeHtml(url)}" alt="${escapeHtml(alt)}"></figure>`;
  };

  md.renderer.rules.heading_open = (tokens, idx, opts, env, self) => {
    const t = tokens[idx];
    const text = tokens[idx + 1].children.map((c) => (c.type === "text" || c.type === "code_inline" ? c.content : "")).join("");
    if (t.tag === "h1") {
      t.attrSet("id", env.id);
    } else {
      let slug = slugify(text);
      const n = env.slugs.get(slug) || 0;
      env.slugs.set(slug, n + 1);
      if (n) slug = `${slug}-${n}`;
      t.attrSet("id", `${env.id}--${slug}`);
    }
    return self.renderToken(tokens, idx, opts);
  };

  const defaultFence = md.renderer.rules.fence;
  md.renderer.rules.fence = (tokens, idx, opts, env, self) => {
    const t = tokens[idx];
    if (t.info.trim() === "mermaid") {
      const n = mermaidBlocks.length;
      mermaidBlocks.push({ file: env.file, index: env.mermaidCount++, source: t.content, svg: null });
      return `<div class="mermaid-figure">@@MERMAID_${n}@@</div>\n`;
    }
    return defaultFence(tokens, idx, opts, env, self);
  };

  // Wrap tables so wide ones can be styled as a unit.
  md.renderer.rules.table_open = () => '<div class="table-wrap"><table>\n';
  md.renderer.rules.table_close = () => "</table></div>\n";
  return md;
}

// --- Citations ----------------------------------------------------------------------

// A chapter's citation table: URL -> { n, title }. The first appearance fixes the number.
function citeNumber(cite, url, title) {
  let e = cite.get(url);
  if (!e) cite.set(url, (e = { n: cite.size + 1, title: null }));
  if (title && !e.title) e.title = title;
  return e.n;
}

// Split a chapter at its "## Sources" heading (outside code fences): [body, sources|null].
// The Sources section runs to the next "## " heading, which stays in the body.
function splitSources(text) {
  const lines = text.split("\n");
  let fence = null;
  let start = -1;
  let end = lines.length;
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(/^\s*(`{3,}|~{3,})/);
    if (m) {
      if (!fence) fence = m[1][0];
      else if (m[1][0] === fence) fence = null;
      continue;
    }
    if (fence) continue;
    if (start < 0 && lines[i].trim() === "## Sources") start = i;
    else if (start >= 0 && /^## /.test(lines[i])) {
      end = i;
      break;
    }
  }
  if (start < 0) return [text, null];
  return [
    [...lines.slice(0, start), ...lines.slice(end)].join("\n"),
    lines.slice(start + 1, end).join("\n"),
  ];
}

// The words around a URL in a Sources line, without separators: "Hooks guide:" -> "Hooks guide".
function cleanLabel(s) {
  let prev;
  s = s.replace(/\(\s*\)/g, " ");
  do {
    prev = s;
    s = s
      .trim()
      .replace(/^(?:[-—–:;,·|]|and\b|or\b)+/i, "")
      .replace(/(?:[-—–:;,·|(]|\band|\bor)+$/i, "")
      .trim();
  } while (s !== prev);
  if (/^\([^()]*\)$/.test(s)) s = s.slice(1, -1).trim();
  return /[\p{L}\p{N}]/u.test(s) ? s : "";
}

// Parse a Sources section: every [text](url) and bare URL becomes a citation (reusing the
// body's number for a URL already cited); lines without a URL are kept as notes.
function parseSources(src, cite) {
  const notes = [];
  for (const line of src.split("\n")) {
    const item = line.match(/^\s*[-*]\s+(.*)$/);
    const text = item ? item[1] : line;
    const re = /\[((?:[^\[\]]|\[[^\]]*\])+)\]\((https?:\/\/[^)\s]+)\)|(https?:\/\/[^\s<>]+)/g;
    const found = [];
    let m;
    let last = 0;
    while ((m = re.exec(text))) {
      let url = m[2] || m[3];
      let len = m[0].length;
      if (m[3]) {
        const trimmed = url.replace(/[.,;:)\]]+$/, "");
        len -= url.length - trimmed.length;
        url = trimmed;
      }
      found.push({ url, linkText: m[1] || null, pre: text.slice(last, m.index) });
      last = m.index + len;
      re.lastIndex = last;
    }
    if (!found.length) {
      notes.push(line);
      continue;
    }
    const head = cleanLabel(found[0].pre);
    // Trailing words describe the URL only as "url (what it is)" with a single URL.
    const rest = text.slice(last).trim();
    const tail = found.length === 1 && /^\(.*\)$/.test(rest) ? cleanLabel(rest) : "";
    for (const f of found) {
      const title = f.linkText || cleanLabel(f.pre) || head || tail || pathTitle(f.url);
      citeNumber(cite, f.url, title);
    }
  }
  return notes.join("\n").trim();
}

// A title for a URL listed without one: its last path segment, "permission-modes" ->
// "Permission modes"; the domain when the path is empty.
function pathTitle(url) {
  const { host, path: p } = shortUrl(url);
  let seg = p.split("/").filter(Boolean).pop();
  if (!seg) return host;
  try {
    seg = decodeURIComponent(seg);
  } catch {}
  seg = seg.replace(/\.(html?|md|pdf)$/i, "").replace(/[-_]+/g, " ").trim();
  return seg ? seg[0].toUpperCase() + seg.slice(1) : host;
}

function shortUrl(url) {
  try {
    const u = new URL(url);
    return { host: u.hostname.replace(/^www\./, ""), path: u.pathname.replace(/\/$/, "") };
  } catch {
    return { host: url, path: "" };
  }
}

// The numbered reference list: "[n] title — domain", each entry a link to its URL. Where
// two entries share a title, the domain gains the last path segment to tell them apart.
function referencesHtml(cite, md) {
  const entries = [...cite.entries()].map(([url, e]) => ({ url, n: e.n, title: e.title || pathTitle(url) })).sort((a, b) => a.n - b.n);
  const count = new Map();
  for (const e of entries) count.set(e.title, (count.get(e.title) || 0) + 1);
  const items = entries.map((e) => {
    const { host, path: p } = shortUrl(e.url);
    let where = host;
    if (count.get(e.title) > 1) {
      const seg = p.split("/").filter(Boolean).pop();
      if (seg) where += `/…/${seg.length > 40 ? seg.slice(0, 38) + "…" : seg}`;
    }
    const title = md.renderInline(e.title.replace(/^\p{Ll}/u, (c) => c.toUpperCase()), { id: "ref" });
    return `<li><a href="${escapeHtml(e.url)}"><span class="ref-n">[${e.n}]</span><span class="ref-body"><span class="ref-title">${title}</span> <span class="ref-host">— ${escapeHtml(where)}</span></span></a></li>`;
  });
  return `<ol class="references">${items.join("")}</ol>`;
}

// Remove the trailing "← Previous · Contents · Next →" line and the rule above it.
function stripFooter(text) {
  const lines = text.replace(/\s+$/, "").split("\n");
  if (lines.length && lines.at(-1).includes("[Contents](README.md)")) {
    lines.pop();
    while (lines.length && lines.at(-1).trim() === "") lines.pop();
    if (lines.length && lines.at(-1).trim() === "---") lines.pop();
  }
  return lines.join("\n") + "\n";
}

// The README becomes the "About this book" front matter: its title and cover image are
// replaced by the cover page, and its Contents section by the generated table of contents.
function aboutMarkdown(text) {
  text = text.replace(/<!--[\s\S]*?-->/g, "");
  text = stripTrailingStartLink(text);
  const lines = text.split("\n");
  const out = ["# About this book", ""];
  let skip = false;
  for (const line of lines) {
    if (/^# /.test(line) || /^!\[[^\]]*\]\(assets\/cover\.svg\)/.test(line)) continue;
    if (/^## /.test(line)) skip = line.trim() === "## Contents";
    if (!skip) out.push(line);
  }
  return out.join("\n");
}
function stripTrailingStartLink(text) {
  const lines = text.replace(/\s+$/, "").split("\n");
  if (lines.at(-1).startsWith("[Start reading")) {
    lines.pop();
    while (lines.length && lines.at(-1).trim() === "") lines.pop();
    if (lines.at(-1).trim() === "---") lines.pop();
  }
  return lines.join("\n") + "\n";
}

// --- Mermaid ------------------------------------------------------------------------

async function renderAllMermaid(browser, blocks) {
  const mermaidConfig = {
    theme: "neutral",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, "Liberation Sans", "DejaVu Sans", sans-serif',
    // Drop shadows are SVG filters, which Chromium rasterises when printing: one bitmap
    // per node. Without them every diagram stays vector and the file stays small.
    themeCSS: "* { filter: none !important; }",
    flowchart: { useMaxWidth: true },
    sequence: { useMaxWidth: true },
  };
  const failures = [];
  const queue = blocks.map((b, i) => [b, i]);
  const worker = async () => {
    while (queue.length) {
      const [b, i] = queue.shift();
      try {
        const { data } = await renderMermaid(browser, b.source, "svg", {
          backgroundColor: "transparent",
          mermaidConfig,
          fontEmbed: false,
          svgId: `mermaid-${i}`,
        });
        // Mermaid's natural size uses 16px labels, larger than the body text; print the
        // diagrams at 75% of it (wide ones still shrink further to fit the text block).
        b.svg = Buffer.from(data)
          .toString("utf8")
          .replace(/^<\?xml[^>]*>\s*/, "")
          .replace(/max-width:\s*([\d.]+)px/, (_, w) => `max-width: ${(Number(w) * 0.75).toFixed(1)}px`);
      } catch (err) {
        failures.push(`book/${b.file} mermaid block ${b.index + 1}: ${String(err.message || err).split("\n")[0]}`);
      }
    }
  };
  await Promise.all(Array.from({ length: 4 }, worker));
  if (failures.length) fail(`${failures.length} Mermaid block(s) failed to render:\n  ${failures.join("\n  ")}`);
}

// --- HTML assembly ------------------------------------------------------------------

function coverHtml(id) {
  const coverSvg = pathToFileURL(path.join(bookDir, "assets", "cover.svg")).href;
  const row = (k, v) => `<tr><th>${k}</th><td>${v}</td></tr>`;
  return `
<section class="cover" id="cover">
  <!-- The artwork carries the title and subtitle as real (searchable) SVG text. -->
  <img class="cover-art" src="${coverSvg}" alt="${escapeHtml(`${BOOK.title}: ${BOOK.subtitle}`)}">
  <p class="cover-author">${escapeHtml(BOOK.author)}</p>
  <table class="cover-meta">
    ${row("Repository", `<a href="${BOOK.repo}">${BOOK.repo}</a>`)}
    ${row("Version", escapeHtml(id.version))}
    ${row("Commit", `<code>${escapeHtml(id.short)}</code> <span class="full-sha">(${escapeHtml(id.commit)})</span>`)}
    ${row("Built", `${escapeHtml(id.timestamp)} (UTC)`)}
    ${row("License", `${BOOK.license} — <a href="${BOOK.licenseUrl}">${BOOK.licenseUrl}</a>`)}
  </table>
</section>`;
}

function tocHtml(parts, titles, online) {
  const entry = (href, label, cls) =>
    `<li class="${cls}"><a href="#${href}"><span class="toc-label">${escapeHtml(label)}</span><span class="toc-dots"></span></a></li>`;
  let html = `<section class="toc" id="toc"><h1>Contents</h1>`;
  html += `<p class="toc-hint">Every entry is a link — click to jump to that page.</p><ul>`;
  html += entry("about", "About this book", "toc-front");
  parts.forEach((p, pi) => {
    html += `<li class="toc-part"><a href="#part-${pi}"><span class="toc-label">${escapeHtml(p.label)}</span><span class="toc-dots"></span></a></li>`;
    for (const g of p.groups) {
      if (g.label) html += `<li class="toc-group">${escapeHtml(g.label)}</li>`;
      for (const f of g.files) html += entry(fileId(f.file), titles.get(f.file), "toc-chapter");
    }
  });
  // The appendices are not printed: they are links to their files in the repository.
  for (const p of online) {
    html += `<li class="toc-part toc-part-online"><span class="toc-label">${escapeHtml(p.label)} (online)</span></li>`;
    for (const f of p.files) {
      html += `<li class="toc-chapter toc-online"><a href="${BOOK.repo}/blob/main/book/${f.file}"><span class="toc-label">${escapeHtml(f.title)}</span><span class="toc-dots"></span><span class="toc-where">github.com ↗</span></a></li>`;
    }
  }
  return html + `</ul></section>`;
}

async function main() {
  const id = buildIdentity();
  log(`version ${id.version}, commit ${id.short}, built ${id.timestamp}`);
  // The appendices part is not printed; the contents links to the files on GitHub.
  const allParts = readingOrder();
  const isAppendices = (p) => /^appendi/i.test(p.label);
  const parts = allParts.filter((p) => !isAppendices(p));
  const online = allParts.filter(isAppendices).map((p) => ({
    label: p.label,
    files: p.groups.flatMap((g) => g.files).map((f) => {
      const h1 = fs.readFileSync(path.join(bookDir, f.file), "utf8").match(/^# (.+)$/m);
      return { ...f, title: h1 ? h1[1].replace(/`/g, "").trim() : f.file };
    }),
  }));
  const files = parts.flatMap((p) => p.groups.flatMap((g) => g.files.map((f) => f.file)));
  const knownFiles = new Set(["README.md", ...files]);
  const mermaidBlocks = [];
  const md = makeRenderer(knownFiles, mermaidBlocks);

  const render = (file, text, cite = null) =>
    md.render(text, { file, id: fileId(file), slugs: new Map(), mermaidCount: 0, cite });
  const titles = new Map();
  const about = render("README.md", aboutMarkdown(fs.readFileSync(path.join(bookDir, "README.md"), "utf8")));
  const chapters = new Map();
  let citations = 0;
  for (const file of files) {
    const text = stripFooter(fs.readFileSync(path.join(bookDir, file), "utf8"));
    const h1 = text.match(/^# (.+)$/m);
    if (!h1) fail(`book/${file} has no '# ' title`);
    titles.set(file, h1[1].replace(/`/g, "").trim());
    // Body first, so its links take the low citation numbers; then the Sources section,
    // whose URLs reuse those numbers or take the next ones.
    const [bodyMd, sourcesMd] = splitSources(text);
    const cite = new Map();
    let html = render(file, bodyMd, cite);
    if (sourcesMd !== null || cite.size) {
      const notes = sourcesMd === null ? "" : parseSources(sourcesMd, cite);
      html += `<section class="sources"><h2 id="${fileId(file)}--sources">Sources</h2>${referencesHtml(cite, md)}`;
      if (notes) html += `<div class="source-notes">${render(file, notes)}</div>`;
      html += `</section>`;
      citations += cite.size;
    }
    chapters.set(file, html);
  }
  log(`${files.length} chapters, ${mermaidBlocks.length} Mermaid blocks, ${citations} numbered sources; appendices online`);

  let body = coverHtml(id) + tocHtml(parts, titles, online) + `<section class="chapter front" id="sec-about">${about}</section>`;
  parts.forEach((p, pi) => {
    body += `<section class="part-title" id="part-${pi}"><h1>${escapeHtml(p.label)}</h1></section>`;
    for (const g of p.groups) for (const f of g.files) body += `<section class="chapter">${chapters.get(f.file)}</section>`;
  });

  // Every in-document link must have a target; Chromium silently drops a link without one.
  const ids = new Set([...body.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]));
  const broken = [...new Set([...body.matchAll(/href="#([^"]+)"/g)].map((m) => m[1]))].filter((h) => !ids.has(h));
  if (broken.length) fail(`links to anchors that do not exist:\n  #${broken.join("\n  #")}`);

  const launchArgs = process.env.CI ? ["--no-sandbox", "--disable-setuid-sandbox"] : [];
  const browser = await puppeteer.launch({ headless: true, args: [...launchArgs, "--allow-file-access-from-files"] });
  try {
    await renderAllMermaid(browser, mermaidBlocks);
    body = body.replace(/@@MERMAID_(\d+)@@/g, (_, n) => mermaidBlocks[Number(n)].svg);

    const css = fs.readFileSync(path.join(here, "book.css"), "utf8");
    // Paged.js is vendored (scripts/pdf/vendor/README.md): the npm package drags in the
    // deprecated @babel/polyfill and core-js@2, which this self-contained bundle never loads.
    const pagedJs = pathToFileURL(path.join(here, "vendor", "paged.polyfill.js")).href;
    const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>${escapeHtml(BOOK.title)}</title>
<style>${css}</style>
<script>window.PagedConfig = { auto: true, after: () => { window.__pagedDone = true; } };</script>
<script src="${pagedJs}"></script>
</head><body>${body}</body></html>`;
    fs.mkdirSync(workDir, { recursive: true });
    const htmlPath = path.join(workDir, "book.html");
    fs.writeFileSync(htmlPath, html);

    log("paginating with Paged.js");
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load", timeout: 120000 });
    await page.waitForFunction("window.__pagedDone === true", { timeout: 600000, polling: 500 });
    if (errors.length) fail(`Paged.js reported errors:\n  ${errors.join("\n  ")}`);
    const pages = await page.evaluate(() => document.querySelectorAll(".pagedjs_page").length);
    const overflow = await page.evaluate(() => {
      // Content wider than the text block means something runs off the page. Paged.js
      // lays each page out in CSS columns, so a block split across pages reports a
      // bounding box spanning several columns; check each fragment and inner scroll width.
      const out = [];
      for (const pg of document.querySelectorAll(".pagedjs_page")) {
        const area = pg.querySelector(".pagedjs_page_content");
        if (!area) continue;
        const width = area.getBoundingClientRect().width + 1;
        for (const el of area.querySelectorAll("pre, table, img, svg, p, li, td, th")) {
          if (el.closest("svg") && el.tagName.toLowerCase() !== "svg") continue;
          const wide = [...el.getClientRects()].some((r) => r.width > width);
          const scrolls = el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible";
          const innerWide = ["PRE", "TD", "TH"].includes(el.tagName) && el.scrollWidth > el.clientWidth + 1;
          if (wide || scrolls || innerWide) {
            out.push(`page ${pg.dataset.pageNumber}: <${el.tagName.toLowerCase()}> ${el.textContent.trim().slice(0, 60)}`);
            break;
          }
        }
      }
      return out;
    });
    if (overflow.length) {
      const msg = `content runs off the page:\n  ${overflow.join("\n  ")}`;
      if (process.env.BOOK_PDF_ALLOW_OVERFLOW) console.warn(`pdf: WARNING: ${msg}`);
      else fail(msg);
    }
    log(`${pages} pages; printing`);
    const rawPdf = path.join(workDir, "book.raw.pdf");
    await page.pdf({ path: rawPdf, preferCSSPageSize: true, printBackground: true, outline: true, tagged: true, timeout: 600000 });
    await page.close();

    execFileSync(
      process.env.PYTHON || "python3",
      [path.join(here, "metadata.py"), rawPdf, OUT_PDF],
      {
        stdio: "inherit",
        env: {
          ...process.env,
          BOOK_TITLE: BOOK.title,
          BOOK_SUBTITLE: BOOK.subtitle,
          BOOK_AUTHOR: BOOK.author,
          BOOK_KEYWORDS: BOOK.keywords,
          BOOK_REPO: BOOK.repo,
          BOOK_LICENSE: BOOK.license,
          BOOK_LICENSE_URL: BOOK.licenseUrl,
          BOOK_COMMIT_RESOLVED: id.commit,
          BOOK_VERSION_RESOLVED: id.version,
          BOOK_BUILD_TIME_RESOLVED: id.timestamp,
          BOOK_CHROME: (await browser.version()).replace("/", " "),
        },
      },
    );
    if (!process.env.BOOK_PDF_KEEP_HTML) fs.rmSync(workDir, { recursive: true, force: true });
  } finally {
    await browser.close();
  }
  const size = (fs.statSync(OUT_PDF).size / 1024 / 1024).toFixed(1);
  log(`wrote ${path.relative(root, OUT_PDF)} (${size} MB)`);
}

main().catch((err) => fail(err.stack || String(err)));
