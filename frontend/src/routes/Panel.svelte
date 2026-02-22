<script>
  import Current from "./Current.svelte";
  import Stats from "./Stats.svelte";
  import Upper from "./Upper.svelte";
  import Lower from "./Lower.svelte";
  import { onMount } from "svelte";

  let currentTime = "";
  let userName = "";
  let mainView = "weight";

  // hardcode for now bc i am the only user
  userName = "ryan";

  onMount(() => {
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  });

  function updateTime() {
    const now = new Date();
    currentTime = now.toLocaleTimeString();
  }
</script>

<div class="bar hover:brightness-110 transition">
  <span>{currentTime}</span>
  <span>user: {userName}</span>
</div>

<div class="layout">
  <div class="top-row">
    <Stats />
    <Current />
  </div>
  <div class="full-row">
    <Lower />
  </div>
  <div class="full-row">
    <Upper />
  </div>
</div>

<style>
  .bar {
    width: min(80vw, 1200px);
    margin: 1vh auto 15vh;
    padding: 0.5rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid var(--bar-border);
    border-radius: 6px;
    background-color: var(--bar-bg);
    color: var(--bar-text);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  }

  .layout {
    max-width: min(80vw, 1200px);
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .top-row {
    display: flex;
    gap: 1.25rem;
    align-items: stretch;
  }

  .top-row > :global(*:first-child) {
    flex: 0 1 35%;
    min-width: 0;
  }
  .top-row > :global(*:last-child) {
    flex: 0 1 65%;
    min-width: 0;
  }

  .full-row {
    display: flex;
    width: 100%;
  }

  .full-row > :global(*) {
    flex: 1 1 100%;
    width: 100%;
    max-width: 100%;
  }

  @media (max-width: 900px) {
    .top-row {
      flex-direction: column;
    }
  }
</style>
