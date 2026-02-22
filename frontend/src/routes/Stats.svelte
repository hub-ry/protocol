<script>
  import { onMount } from "svelte";

  let weights = [];
  let firstDate = "Loading...";
  let currDate = "Loading...";
  let daysDifference = "Loading...";
  let goalWeight = 188;

  onMount(async () => {
    const res = await fetch("http://100.89.197.38:5000/weights");
    weights = await res.json();
    if (weights.length > 0) {
      firstDate = weights[0].date;
      currDate = new Date().toISOString().split("T")[0];
      const start = new Date(firstDate);
      const end = new Date(currDate);
      daysDifference = Math.floor((end - start) / (1000 * 60 * 60 * 24));
    }
  });
  $: latestWeight = weights[weights.length - 1];
</script>

<div class="stats-box">
  <header class="stats-header">
    <h2 class="stats-title">Stats</h2>
  </header>

  <div class="stats-body">
    <dl class="stat-list">
      <div class="stat-row">
        <dt class="stat-label">Start date</dt>
        <dd class="stat-value">{firstDate}</dd>
      </div>
      <div class="stat-row">
        <dt class="stat-label">Current date</dt>
        <dd class="stat-value">{currDate}</dd>
      </div>
      <div class="stat-row">
        <dt class="stat-label">Days elapsed</dt>
        <dd class="stat-value">{daysDifference}</dd>
      </div>
      <div class="stat-row stat-row--highlight">
        <dt class="stat-label">Current weight</dt>
        <dd class="stat-value stat-value--primary">
          {latestWeight?.weight ?? "—"} <span class="stat-unit">lbs</span>
        </dd>
      </div>
      <div class="stat-row">
        <dt class="stat-label">Goal weight</dt>
        <dd class="stat-value">{goalWeight} <span class="stat-unit">lbs</span></dd>
      </div>
      <div class="stat-row">
        <dt class="stat-label">Status</dt>
        <dd class="stat-value stat-value--badge">Weight loss</dd>
      </div>
    </dl>
  </div>
</div>

<style>
  .stats-box {
    display: flex;
    flex-direction: column;
    min-height: 0;
    border: 1px solid var(--card-border);
    border-radius: 10px;
    background-color: var(--card-bg);
    box-shadow: var(--card-shadow);
    overflow: hidden;
  }

  .stats-header {
    flex-shrink: 0;
    padding: 0.875rem 1rem;
    border-bottom: 1px solid var(--card-border);
    background: rgba(0, 0, 0, 0.2);
  }

  .stats-title {
    margin: 0;
    font-size: 0.8125rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--label-muted);
  }

  .stats-body {
    flex: 1;
    padding: 1rem;
    min-height: 0;
  }

  .stat-list {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .stat-row {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: baseline;
    gap: 0.75rem;
  }

  .stat-row--highlight {
    padding: 0.5rem 0;
    margin: 0.25rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .stat-label {
    margin: 0;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--label-muted);
  }

  .stat-value {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 500;
    color: rgb(226, 232, 240);
    text-align: right;
  }

  .stat-value--primary {
    font-size: 1rem;
    font-weight: 600;
    color: rgb(234, 179, 8);
  }

  .stat-value--badge {
    font-size: 0.75rem;
    color: rgb(134, 239, 172);
  }

  .stat-unit {
    font-size: 0.75em;
    font-weight: 400;
    color: var(--label-muted);
  }
</style>
