"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { AlertsTicker } from "@/components/alerts-ticker"
import { CommoditySignals } from "@/components/commodity-signals"
import { GeospatialMap } from "@/components/geospatial-map"
import { RegulatoryScanner } from "@/components/regulatory-scanner"
import { SignalsTimeline } from "@/components/signals-timeline"
import { mockSignals } from "@/lib/mock-data"

export default function CracksPage() {
  const [signals, setSignals] = useState([])
  const [selectedSignal, setSelectedSignal] = useState(null)

  useEffect(() => {
    // Filter signals for cracks/refinery-related content
    const cracksSignals = mockSignals.filter(
      (signal) =>
        signal.commodity?.toLowerCase().includes("oil") ||
        signal.commodity?.toLowerCase().includes("gas") ||
        signal.headline.toLowerCase().includes("refinery") ||
        signal.headline.toLowerCase().includes("diesel") ||
        signal.headline.toLowerCase().includes("gasoline") ||
        signal.headline.toLowerCase().includes("crack") ||
        signal.headline.toLowerCase().includes("spread"),
    )
    setSignals(cracksSignals)

    const interval = setInterval(() => {
      setSignals((prev) =>
        prev.map((signal) => ({
          ...signal,
          score: Math.max(70, Math.min(95, signal.score + (Math.random() - 0.5) * 4)),
        })),
      )
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground dark">
      <Navigation />
      <div className="terminal-grid">
        <div className="ticker-area">
          <AlertsTicker signals={signals} />
        </div>

        <div className="signals-area">
          <CommoditySignals signals={signals} onSignalSelect={setSelectedSignal} selectedSignal={selectedSignal} />
        </div>

        <div className="map-area">
          <GeospatialMap signals={signals} selectedSignal={selectedSignal} onSignalSelect={setSelectedSignal} />
        </div>

        <div className="scanner-area">
          <RegulatoryScanner signals={signals} />
        </div>

        <div className="timeline-area">
          <SignalsTimeline signals={signals} />
        </div>
      </div>
    </div>
  )
}
