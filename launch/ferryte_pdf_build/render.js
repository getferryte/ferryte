const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const MarkdownIt = require("markdown-it");
const puppeteer = require("puppeteer-core");

const buildDir = __dirname;
const inputPath = path.resolve(buildDir, "../ferryte_the_complete_guide.md");
const htmlPath = path.resolve(buildDir, "ferryte_the_complete_guide_readable.html");
const pdfPath = path.resolve(buildDir, "../ferryte_the_complete_guide_readable.pdf");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function countTables(markdown) {
  const lines = markdown.split(/\r?\n/);
  let count = 0;
  for (let index = 1; index < lines.length; index += 1) {
    if (/^\|.*\|$/.test(lines[index - 1]) && /^\|[\s:|\-]+$/.test(lines[index])) {
      count += 1;
    }
  }
  return count;
}

function countLines(markdown) {
  if (markdown.length === 0) {
    return 0;
  }
  const lines = markdown.split(/\r?\n/).length;
  return markdown.endsWith("\n") ? lines - 1 : lines;
}

function extractSubtitle(markdown) {
  const match = markdown.match(/^###\s+(.+)$/m);
  return match ? match[1].replace(/^From\s+/, "") : "Complete guide";
}

function normalizeMermaidForRendering(source) {
  if (!/^sequenceDiagram\b/m.test(source)) {
    return source;
  }

  return source
    .replace(/\bparticipant Note as/g, "participant Notebook as")
    .replace(/->>Note\b/g, "->>Notebook")
    .replace(/-->>Note\b/g, "-->>Notebook")
    .replace(/\bNote-->>/g, "Notebook-->>")
    .replace(/\bNote->>/g, "Notebook->>");
}

async function main() {
  const markdown = fs.readFileSync(inputPath, "utf8");
  const diagramSources = [];

  const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
  });

  const defaultFence = md.renderer.rules.fence;
  md.renderer.rules.fence = (tokens, idx, options, env, self) => {
    const token = tokens[idx];
    const info = token.info.trim().split(/\s+/)[0];
    if (info === "mermaid") {
      const number = diagramSources.push(token.content);
      return [
        `<figure class="diagram-block" data-diagram="${number}">`,
        `<figcaption>Diagram ${number}</figcaption>`,
        `<div class="mermaid-source">${escapeHtml(token.content)}</div>`,
        `</figure>`,
      ].join("");
    }
    return defaultFence(tokens, idx, options, env, self);
  };

  const rendered = md.render(markdown);
  const lineCount = countLines(markdown);
  const diagramCount = diagramSources.length;
  const tableCount = countTables(markdown);
  const subtitle = extractSubtitle(markdown);

  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ferryte: The Complete Guide</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 15mm 20mm 15mm;
    }

    * {
      box-sizing: border-box;
    }

    html {
      font-size: 16px;
    }

    body {
      margin: 0;
      background: #ffffff;
      color: #1d2730;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      line-height: 1.58;
    }

    .page {
      max-width: 880px;
      margin: 0 auto;
      padding: 0;
    }

    .cover {
      min-height: 245mm;
      display: flex;
      flex-direction: column;
      justify-content: center;
      border-bottom: 4px solid #14746f;
      page-break-after: always;
    }

    .cover-kicker {
      color: #14746f;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .cover h1 {
      margin: 12px 0 10px;
      color: #102a2f;
      font-size: 54px;
      line-height: 1.03;
    }

    .cover-subtitle {
      max-width: 680px;
      color: #496169;
      font-size: 19px;
      line-height: 1.45;
    }

    .cover-meta {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 34px;
    }

    .meta-card {
      min-height: 72px;
      padding: 14px 14px 12px;
      border: 1px solid #d7e3e4;
      border-radius: 8px;
      background: #f7fbfb;
    }

    .meta-label {
      color: #657880;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .meta-value {
      margin-top: 3px;
      color: #163238;
      font-size: 18px;
      font-weight: 800;
    }

    .reader-note {
      margin: 0 0 22px;
      padding: 14px 16px;
      border-left: 5px solid #14746f;
      background: #eef8f7;
      color: #24383e;
      page-break-inside: avoid;
    }

    .reader-note strong {
      color: #102a2f;
    }

    h1, h2, h3 {
      color: #102a2f;
      line-height: 1.18;
    }

    main > h1 {
      margin: 0 0 16px;
      padding-top: 4px;
      font-size: 34px;
      page-break-before: always;
      border-bottom: 3px solid #14746f;
      padding-bottom: 10px;
    }

    main > h1:first-of-type {
      page-break-before: auto;
    }

    h2 {
      margin: 28px 0 10px;
      font-size: 24px;
    }

    h3 {
      margin: 22px 0 8px;
      font-size: 18px;
    }

    p {
      margin: 0 0 12px;
    }

    hr {
      margin: 24px 0;
      border: 0;
      border-top: 1px solid #d7e3e4;
    }

    a {
      color: #0b6f9d;
      text-decoration: none;
    }

    ul, ol {
      margin: 8px 0 14px 24px;
      padding: 0;
    }

    li {
      margin: 5px 0;
      padding-left: 2px;
    }

    blockquote {
      margin: 14px 0 18px;
      padding: 13px 16px;
      border-left: 5px solid #12a594;
      border-radius: 0 8px 8px 0;
      background: #eefaf8;
      color: #20383d;
      page-break-inside: avoid;
    }

    blockquote p:last-child {
      margin-bottom: 0;
    }

    code {
      padding: 1px 4px;
      border-radius: 4px;
      background: #eef2f3;
      color: #163238;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 0.92em;
    }

    pre {
      overflow: auto;
      margin: 14px 0 18px;
      padding: 12px 14px;
      border: 1px solid #d7e3e4;
      border-radius: 8px;
      background: #f7fafb;
      color: #16272d;
      font-size: 12px;
      line-height: 1.48;
      white-space: pre-wrap;
      word-break: break-word;
      page-break-inside: avoid;
    }

    pre code {
      padding: 0;
      background: transparent;
      font-size: inherit;
    }

    table {
      width: 100%;
      margin: 14px 0 22px;
      border-collapse: collapse;
      font-size: 12.3px;
      line-height: 1.42;
      page-break-inside: avoid;
    }

    th {
      background: #143d43;
      color: #ffffff;
      font-weight: 800;
      text-align: left;
    }

    th, td {
      padding: 8px 9px;
      border: 1px solid #cfdcde;
      vertical-align: top;
    }

    tr:nth-child(even) td {
      background: #f6f9fa;
    }

    .diagram-block {
      margin: 18px 0 24px;
      padding: 14px;
      border: 1px solid #cddfe2;
      border-radius: 8px;
      background: #fbfdfd;
      page-break-inside: avoid;
    }

    .diagram-block figcaption {
      margin-bottom: 8px;
      color: #526a72;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .mermaid-source {
      width: 100%;
      text-align: center;
    }

    .mermaid-source svg {
      max-width: 100%;
      height: auto;
    }

    .diagram-error {
      color: #8a2f2f;
      font-weight: 700;
    }

    strong {
      color: #102a2f;
    }

    @media print {
      .page {
        max-width: none;
      }

      a {
        color: #0a5e82;
      }

      .diagram-block, blockquote, table, pre {
        break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="cover">
      <div class="cover-kicker">Reader-friendly PDF edition</div>
      <h1>Ferryte: The Complete Guide</h1>
      <p class="cover-subtitle">${escapeHtml(subtitle)}</p>
      <div class="cover-meta" aria-label="Document preservation summary">
        <div class="meta-card">
          <div class="meta-label">Source lines</div>
          <div class="meta-value">${lineCount}</div>
        </div>
        <div class="meta-card">
          <div class="meta-label">Diagrams</div>
          <div class="meta-value">${diagramCount}</div>
        </div>
        <div class="meta-card">
          <div class="meta-label">Tables</div>
          <div class="meta-value">${tableCount}</div>
        </div>
      </div>
    </section>

    <main>
      <aside class="reader-note">
        <strong>Preservation note:</strong> this PDF keeps the original guide content intact and adds print styling for readability. Mermaid code blocks are rendered as diagrams, while the source Markdown file remains unchanged.
      </aside>
      ${rendered}
    </main>
  </div>

  <script src="node_modules/mermaid/dist/mermaid.min.js"></script>
  <script>
    function escapeForPre(value) {
      return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function normalizeMermaidForRendering(source) {
      if (!/^sequenceDiagram\\b/m.test(source)) {
        return source;
      }

      return source
        .replace(/\\bparticipant Note as/g, "participant Notebook as")
        .replace(/->>Note\\b/g, "->>Notebook")
        .replace(/-->>Note\\b/g, "-->>Notebook")
        .replace(/\\bNote-->>/g, "Notebook-->>")
        .replace(/\\bNote->>/g, "Notebook->>");
    }

    async function renderMermaidBlocks() {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "loose",
        theme: "base",
        themeVariables: {
          background: "#fbfdfd",
          primaryColor: "#e7f6f4",
          primaryTextColor: "#123238",
          primaryBorderColor: "#14746f",
          lineColor: "#14746f",
          secondaryColor: "#f5fbfb",
          tertiaryColor: "#ffffff",
          fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"
        },
        flowchart: {
          htmlLabels: true,
          curve: "basis",
          useMaxWidth: true
        },
        sequence: {
          useMaxWidth: true,
          wrap: true
        }
      });

      const blocks = Array.from(document.querySelectorAll(".mermaid-source"));
      for (let index = 0; index < blocks.length; index += 1) {
        const block = blocks[index];
        const source = normalizeMermaidForRendering(block.textContent.trim());
        try {
          const result = await mermaid.render("mermaid-render-" + index, source);
          block.innerHTML = result.svg;
          block.classList.add("mermaid-rendered");
          if (result.bindFunctions) {
            result.bindFunctions(block);
          }
        } catch (error) {
          block.classList.add("diagram-error");
          block.innerHTML = "<p>Diagram render failed; original Mermaid source is preserved below.</p><pre>" + escapeForPre(source) + "</pre>";
          console.error("Mermaid render failed", index, error);
        }
      }
      window.__mermaidDone = true;
    }

    window.__mermaidDone = false;
    window.addEventListener("load", renderMermaidBlocks);
  </script>
</body>
</html>`;

  fs.writeFileSync(htmlPath, html, "utf8");

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: "new",
    args: [
      "--allow-file-access-from-files",
      "--disable-web-security",
      "--no-sandbox"
    ],
  });

  const page = await browser.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") {
      console.error(message.text());
    }
  });

  await page.goto(pathToFileURL(htmlPath).href, {
    waitUntil: "networkidle0",
    timeout: 60000,
  });
  await page.waitForFunction("window.__mermaidDone === true", { timeout: 60000 });

  const failedDiagrams = await page.$$eval(".diagram-error", (nodes) => nodes.length);
  if (failedDiagrams > 0) {
    throw new Error(`${failedDiagrams} Mermaid diagram(s) failed to render`);
  }

  await page.emulateMediaType("print");
  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: "<div></div>",
    footerTemplate: "<div style='width:100%;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;font-size:9px;color:#6b7d83;text-align:center;'>Ferryte: The Complete Guide &nbsp;|&nbsp; <span class='pageNumber'></span> / <span class='totalPages'></span></div>",
    margin: {
      top: "0",
      right: "0",
      bottom: "0",
      left: "0",
    },
  });

  await browser.close();

  console.log(JSON.stringify({
    inputPath,
    htmlPath,
    pdfPath,
    lineCount,
    diagramCount,
    tableCount,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
