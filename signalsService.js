// src/services/signalsService.js

// Toggle this to "true" for demo mode (uses static JSON), or "false" for backend API.
const USE_DEMO_DATA = true;

// Demo JSON file (place agrisignals_demo_signals.json in /public)
const DEMO_URL = "/agrisignals_demo_signals.json";

// Backend API (FastAPI or your service endpoint)
const API_BASE_URL = "https://api.agrisignals.com/api";

export async function fetchLatestSignals(limit = 10) {
  if (USE_DEMO_DATA) {
    const res = await fetch(DEMO_URL);
    return res.json();
  } else {
    const res = await fetch(`${API_BASE_URL}/signals/latest?limit=${limit}`);
    return res.json();
  }
}

export async function fetchSignalById(id) {
  if (USE_DEMO_DATA) {
    const res = await fetch(DEMO_URL);
    const all = await res.json();
    return all.find(sig => sig.id === id);
  } else {
    const res = await fetch(`${API_BASE_URL}/signals/${id}`);
    return res.json();
  }
}

export async function fetchAlphaForSignal(id) {
  if (USE_DEMO_DATA) {
    // Demo mode: construct alpha inline
    const sig = await fetchSignalById(id);
    return {
      headline: sig.headline,
      so_what: sig.so_what,
      who_bleeds: sig.who_bleeds,
      who_benefits: sig.who_benefits,
      tradecraft: sig.tradecraft
    };
  } else {
    const res = await fetch(`${API_BASE_URL}/signals/${id}/alpha`);
    return res.json();
  }
}

