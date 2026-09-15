(() => {
  "use strict";

  document.documentElement.dataset.bsTheme = "dark";

  const segments = window.location.pathname.split("/").filter(Boolean);
  const channel = segments.includes("develop") ? "develop" : "main";
  document.body.dataset.releaseChannel = channel;

  const brand = document.querySelector(".navbar-brand");
  if (brand) {
    const badge = document.createElement("span");
    badge.className = "release-badge";
    badge.innerHTML = `<span aria-hidden="true"></span>${channel === "main" ? "__PRODUCTION_LABEL__" : "__PREVIEW_LABEL__"}`;
    brand.insertAdjacentElement("afterend", badge);
  }

  const primaryNav = document.querySelector("#navbar-collapse .navbar-nav");
  if (primaryNav) {
    const pagesRoot = "__PAGES_ROOT__";
    primaryNav.querySelectorAll("a.nav-link").forEach((link) => {
      if (link.textContent.trim() === "Home") {
        link.href = pagesRoot;
      } else {
        link.closest("li")?.remove();
      }
    });
    for (const [label, target] of [["__PRODUCTION_LABEL__", "main"], ["__PREVIEW_LABEL__", "develop"]]) {
      const item = document.createElement("li");
      item.className = "nav-item";
      const link = document.createElement("a");
      link.className = `nav-link channel-link${channel === target ? " active" : ""}`;
      link.href = `${pagesRoot}${target}/`;
      link.textContent = label;
      item.append(link);
      primaryNav.append(item);
    }
    document.querySelectorAll("[data-release-target]").forEach((link) => {
      link.href = `${pagesRoot}${link.dataset.releaseTarget}/`;
    });
  }

  const editLink = [...document.querySelectorAll("a.nav-link")].find((link) =>
    link.textContent.includes("Edit on GitHub"),
  );
  if (editLink) {
    editLink.href = editLink.href.replace("/edit/main/", `/edit/${channel}/`);
  }

  const footer = document.querySelector("footer.col-md-12");
  if (footer) {
    const provenance = document.createElement("p");
    provenance.className = "release-provenance";
    provenance.innerHTML = [
      `<strong>Provenance</strong>`,
      `<a href="__REPOSITORY_URL__/tree/__RELEASE_SHA__">__REPOSITORY__@__SHORT_SHA__</a>`,
      `<span>branch / __RELEASE_BRANCH__</span>`,
      `<span>channel / __RELEASE_CHANNEL__</span>`,
      `<span>Made with ❤️ by <a href="https://the-vibey-project.github.io/vibey/">Vibey</a>, Developed by <a href="https://vibewithadam.matthewsteinberger.com/">Adam Matthew Steinberger</a> (<a href="https://github.com/adammatthewsteinberger/">@adammatthewsteinberger</a>).</span>`,
    ].join('<span aria-hidden="true">·</span>');
    footer.append(provenance);
  }

  // The documentation's own downloadable forms — the research paper and the book — are
  // published beside the pages they mirror: release-surfaces copies paper.pdf, paper/,
  // book.epub, book.pdf and book-print.html into the channel site. Which of them exist on
  // THIS deploy is substituted below from file presence in the built site, never from
  // configuration, so a link is never rendered to something that was not produced. An
  // unsubstituted placeholder (an older workflow) degrades to "nothing to show".
  const surfacesRaw = '__DOC_SURFACES__';
  const surfaces = surfacesRaw.startsWith("{") ? JSON.parse(surfacesRaw) : {};
  const channelRoot = `__PAGES_ROOT__${channel}/`;
  const surfaceLinks = (items) =>
    items
      .filter(([present]) => present)
      .map(([, label, file]) => `<a href="${channelRoot}${file}">${label}</a>`)
      .join(' <span aria-hidden="true">·</span> ');
  const paperLinks = surfaceLinks([
    [surfaces.paper_pdf, "PDF", "paper.pdf"],
    [surfaces.paper_html, "HTML", "paper/"],
  ]);
  // The governance corpus (sub-doctrine 7.b), in the order of authority, linked only for the
  // pages this deploy actually published.
  const governanceNames = {
    constitution: "Constitution",
    doctrines: "Doctrines",
    commandments: "Commandments",
    "bill-of-rights": "Bill of Rights",
  };
  const governanceOrder = ["constitution", "doctrines", "commandments", "bill-of-rights"];
  // Slugs come from repository file names: only plain ones are linked, the URL component is
  // encoded and the label escaped, so a name can never inject markup into a page.
  const publishedGovernance = (Array.isArray(surfaces.governance) ? surfaces.governance : []).filter(
    (slug) => typeof slug === "string" && /^[a-z0-9][a-z0-9-]*$/.test(slug),
  );
  const escapeText = (text) =>
    String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const governancePages = [
    ...governanceOrder.filter((slug) => publishedGovernance.includes(slug)),
    ...publishedGovernance.filter((slug) => !governanceOrder.includes(slug)).sort(),
  ];
  const governanceLinks = governancePages
    .map(
      (slug) =>
        `<a href="${channelRoot}governance/${encodeURIComponent(slug)}/">${escapeText(governanceNames[slug] || slug.replace(/^(sd-\d+).*$/i, "$1").toUpperCase())}</a>`,
    )
    .join(' <span aria-hidden="true">·</span> ');
  const bookLinks = surfaceLinks([
    [surfaces.book_pdf, "PDF", "book.pdf"],
    [surfaces.book_epub, "EPUB", "book.epub"],
    [surfaces.book_print, "print HTML", "book-print.html"],
  ]);

  // One click from every page: a Paper and a Book entry in the primary navigation.
  if (primaryNav) {
    const bookTarget = surfaces.book_pdf
      ? "book.pdf"
      : surfaces.book_epub
        ? "book.epub"
        : "book-print.html";
    for (const [label, present, file] of [
      ["Governance", governancePages.length > 0, `governance/${encodeURIComponent(governancePages[0] || "")}/`],
      ["Paper", Boolean(paperLinks), surfaces.paper_html ? "paper/" : "paper.pdf"],
      ["Book", Boolean(bookLinks), bookTarget],
    ]) {
      if (!present) continue;
      const item = document.createElement("li");
      item.className = "nav-item";
      const link = document.createElement("a");
      link.className = "nav-link surface-link";
      link.href = `${channelRoot}${file}`;
      link.textContent = label;
      item.append(link);
      primaryNav.append(item);
    }
  }

  // And on every page's footer, beside the provenance line, every format that exists.
  if (footer && (paperLinks || bookLinks || governanceLinks)) {
    const reading = document.createElement("p");
    reading.className = "release-surfaces";
    reading.innerHTML = [
      governanceLinks ? `<strong>Governance</strong> ${governanceLinks}` : "",
      paperLinks ? `<strong>Research paper</strong> ${paperLinks}` : "",
      bookLinks ? `<strong>The book</strong> ${bookLinks}` : "",
    ]
      .filter(Boolean)
      .join('<span aria-hidden="true">·</span>');
    footer.append(reading);
  }
})();
