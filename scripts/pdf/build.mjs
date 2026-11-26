#!/usr/bin/env node
// Build the whole book as one PDF: dist/AI-Native Development.pdf
//
// Run it with `make pdf` (which runs `npm ci` first when node_modules is missing).
//
// Pipeline:
//   1. Read the reading order from the "## Contents" tables in book/README.md.
//   2. Render each Markdown file to HTML with markdown-it. The footer navigation line is
//      dropped and links between chapters become in-document anchors.
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
  const md = new MarkdownIt({ html: false, linkify: false, typographer: false });
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

  md.renderer.rules.link_open = (tokens, idx, opts, env, self) => {
    const t = tokens[idx];
    t.attrSet("href", resolveHref(t.attrGet("href"), env));
    return self.renderToken(tokens, idx, opts);
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

function tocHtml(parts, titles) {
  const entry = (href, label, cls) =>
    `<li class="${cls}"><a href="#${href}"><span class="toc-label">${escapeHtml(label)}</span><span class="toc-dots"></span></a></li>`;
  let html = `<section class="toc" id="toc"><h1>Contents</h1><ul>`;
  html += entry("about", "About this book", "toc-front");
  parts.forEach((p, pi) => {
    html += `<li class="toc-part"><a href="#part-${pi}"><span class="toc-label">${escapeHtml(p.label)}</span><span class="toc-dots"></span></a></li>`;
    for (const g of p.groups) {
      if (g.label) html += `<li class="toc-group">${escapeHtml(g.label)}</li>`;
      for (const f of g.files) html += entry(fileId(f.file), titles.get(f.file), "toc-chapter");
    }
  });
  return html + `</ul></section>`;
}

async function main() {
  const id = buildIdentity();
  log(`version ${id.version}, commit ${id.short}, built ${id.timestamp}`);
  const parts = readingOrder();
  const files = parts.flatMap((p) => p.groups.flatMap((g) => g.files.map((f) => f.file)));
  const knownFiles = new Set(["README.md", ...files]);
  const mermaidBlocks = [];
  const md = makeRenderer(knownFiles, mermaidBlocks);

  const render = (file, text) => md.render(text, { file, id: fileId(file), slugs: new Map(), mermaidCount: 0 });
  const titles = new Map();
  const about = render("README.md", aboutMarkdown(fs.readFileSync(path.join(bookDir, "README.md"), "utf8")));
  const chapters = new Map();
  for (const file of files) {
    const text = stripFooter(fs.readFileSync(path.join(bookDir, file), "utf8"));
    const h1 = text.match(/^# (.+)$/m);
    if (!h1) fail(`book/${file} has no '# ' title`);
    titles.set(file, h1[1].replace(/`/g, "").trim());
    chapters.set(file, render(file, text));
  }
  log(`${files.length} chapters and appendices, ${mermaidBlocks.length} Mermaid blocks`);

  let body = coverHtml(id) + tocHtml(parts, titles) + `<section class="chapter front" id="sec-about">${about}</section>`;
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
    const pagedJs = pathToFileURL(path.join(root, "node_modules", "pagedjs", "dist", "paged.polyfill.js")).href;
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
