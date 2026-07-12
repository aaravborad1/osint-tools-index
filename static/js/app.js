(function () {
  const input = document.getElementById("search-input");
  const results = document.getElementById("search-results");
  const count = document.getElementById("search-count");
  if (!input) return;

  let all = [];
  let loaded = false;

  fetch("data/tools.json")
    .then((r) => r.json())
    .then((data) => {
      data.categories.forEach((cat) => {
        cat.tools.forEach((t) => {
          all.push({ name: t.name, url: t.url, category: cat.name, slug: cat.slug, status: t.status });
        });
      });
      loaded = true;
      if (input.value.trim()) render(input.value.trim());
    })
    .catch(() => {
      count.textContent = "Search index failed to load.";
    });

  function stampFor(status) {
    if (status === "alive") return '<span class="stamp alive mono">LIVE</span>';
    if (status === "dead") return '<span class="stamp dead mono">DEAD</span>';
    return '<span class="stamp unknown mono">UNCHECKED</span>';
  }

  function render(query) {
    if (!loaded) return;
    const q = query.toLowerCase();
    const matches = all.filter(
      (t) => t.name.toLowerCase().includes(q) || t.url.toLowerCase().includes(q)
    ).slice(0, 60);

    count.textContent = query
      ? `${matches.length} match${matches.length === 1 ? "" : "es"} for "${query}"`
      : "";

    results.innerHTML = matches
      .map(
        (t) => `
        <div class="result-row">
          <span>
            <a class="tool-link" href="${t.url}" target="_blank" rel="noopener">${escapeHtml(t.name)}</a>
            <span class="url mono">${escapeHtml(t.url)}</span>
          </span>
          <span style="display:flex; align-items:center; gap:0.6rem;">
            <a class="cat" href="category/${t.slug}.html">${escapeHtml(t.category)}</a>
            ${stampFor(t.status)}
          </span>
        </div>`
      )
      .join("");
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  let debounce;
  input.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => render(input.value.trim()), 120);
  });
})();
