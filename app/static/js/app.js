(function () {
  "use strict";

  const AURA = window.__AURA__ || { dictionary: {}, initialSnapshot: null, lang: "en" };
  const t = AURA.dictionary || {};

  const form = document.getElementById("analyze-form");
  const cityInput = document.getElementById("city-select");
  const productInput = document.getElementById("product-input");
  const submitBtn = document.getElementById("submit-btn");

  const els = {
    avgPrice: document.getElementById("kpi-avg-price"),
    demand: document.getElementById("kpi-demand"),
    saturation: document.getElementById("kpi-saturation"),
    opportunity: document.getElementById("kpi-opportunity"),
    generatedAt: document.getElementById("generated-at"),
    competitorCount: document.getElementById("competitor-count"),
    competitorList: document.getElementById("competitor-list"),
    insightPanel: document.getElementById("insight-panel"),
    trendCaption: document.getElementById("trend-caption"),
  };

  function formatIDR(n) {
    return "Rp " + Number(n).toLocaleString("id-ID").replace(/,/g, ".");
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ---- Chart -------------------------------------------------------
  let chart = null;

  function initialTrend() {
    const snap = AURA.initialSnapshot;
    if (!snap) return { labels: [], price: [], demand: [] };
    return {
      labels: snap.trend.map((p) => p.label),
      price: snap.trend.map((p) => p.price),
      demand: snap.trend.map((p) => p.demand),
    };
  }

  function buildChart() {
    const ctx = document.getElementById("trend-chart");
    if (!ctx || typeof Chart === "undefined") return;
    const data = initialTrend();

    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: t.trend_price_series || "Price",
            data: data.price,
            borderColor: "#C9A15A",
            backgroundColor: "rgba(201,161,90,0.12)",
            yAxisID: "yPrice",
            tension: 0.35,
            fill: true,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: t.trend_demand_series || "Demand",
            data: data.demand,
            borderColor: "#3FA796",
            backgroundColor: "rgba(63,167,150,0.10)",
            yAxisID: "yDemand",
            tension: 0.35,
            fill: false,
            pointRadius: 0,
            borderWidth: 2,
            borderDash: [4, 3],
          },
        ],
      },
      options: {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { display: false } },
        scales: {
          x: {
            grid: { color: "#2A3240" },
            ticks: { color: "#97A0AF", font: { size: 10 } },
          },
          yPrice: {
            position: "left",
            grid: { color: "#2A3240" },
            ticks: {
              color: "#97A0AF",
              font: { size: 10 },
              callback: (v) => (v / 1000).toFixed(0) + "k",
            },
          },
          yDemand: {
            position: "right",
            min: 0,
            max: 100,
            grid: { display: false },
            ticks: { color: "#97A0AF", font: { size: 10 } },
          },
        },
      },
    });
  }

  function updateChart(snapshot) {
    if (!chart) return;
    chart.data.labels = snapshot.trend.map((p) => p.label);
    chart.data.datasets[0].data = snapshot.trend.map((p) => p.price);
    chart.data.datasets[1].data = snapshot.trend.map((p) => p.demand);
    chart.update();
  }

  // ---- Render --------------------------------------------------------
  function renderCompetitors(competitors) {
    if (!els.competitorList) return;
    const salesLabel = t.competitor_table_sales || "sales (30d)";
    els.competitorList.innerHTML = competitors
      .map(
        (c, i) => `
      <li class="flex items-center gap-3 px-4 py-3 fade-in">
        <span class="font-headline text-aura-dim text-sm w-4 text-center">${i + 1}</span>
        <div class="flex-1 min-w-0">
          <div class="text-sm truncate">${escapeHtml(c.name)}</div>
          <div class="text-xs text-aura-dim">★ ${c.rating} · ${c.sales_last_30d} ${escapeHtml(salesLabel)}</div>
        </div>
        <div class="text-sm font-medium whitespace-nowrap">${formatIDR(c.price)}</div>
      </li>`
      )
      .join("");
  }

  function sentimentBorderClass(snapshot) {
    if (snapshot.opportunity_score >= 65) return "border-aura-gold";
    if (snapshot.opportunity_score <= 35) return "border-aura-risk";
    return "border-aura-teal";
  }

  function render(snapshot) {
    if (els.avgPrice) els.avgPrice.textContent = formatIDR(snapshot.avg_price);
    if (els.demand) els.demand.innerHTML = snapshot.demand_index + '<span class="text-sm text-aura-dim">/100</span>';
    if (els.saturation) els.saturation.innerHTML = snapshot.market_saturation + '<span class="text-sm text-aura-dim">/100</span>';
    if (els.opportunity) els.opportunity.innerHTML = snapshot.opportunity_score + '<span class="text-sm text-aura-dim">/100</span>';
    if (els.generatedAt) els.generatedAt.textContent = snapshot.generated_at;
    if (els.competitorCount) els.competitorCount.textContent = snapshot.competitor_count;
    if (els.trendCaption) els.trendCaption.textContent = snapshot.city_label + " · " + snapshot.product;

    if (els.insightPanel) {
      els.insightPanel.classList.remove("border-aura-gold", "border-aura-teal", "border-aura-risk");
      els.insightPanel.classList.add(sentimentBorderClass(snapshot));
      els.insightPanel.textContent = snapshot.insight_text;
      els.insightPanel.classList.remove("fade-in");
      void els.insightPanel.offsetWidth;
      els.insightPanel.classList.add("fade-in");
    }

    renderCompetitors(snapshot.competitors);
    updateChart(snapshot);
  }

  // ---- Networking ------------------------------------------------
  async function runAnalysis(city, product) {
    if (!form) return;
    submitBtn.disabled = true;
    const originalLabel = submitBtn.innerHTML;
    submitBtn.innerHTML = `<span>${escapeHtml(t.loading_text || "Loading...")}</span>`;

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, product, language: AURA.lang || "en" }),
      });
      if (!res.ok) throw new Error("bad response");
      const snapshot = await res.json();
      render(snapshot);
    } catch (err) {
      if (els.insightPanel) {
        els.insightPanel.textContent = t.error_generic || "Something went wrong.";
      }
      console.error("Aura Intel analysis failed:", err);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalLabel;
    }
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      runAnalysis(cityInput.value, productInput.value.trim() || productInput.placeholder);
    });
  }

  document.querySelectorAll("[data-quick-product]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const product = btn.getAttribute("data-quick-product");
      if (productInput) productInput.value = product;
      runAnalysis(cityInput.value, product);
    });
  });

  buildChart();
})();
