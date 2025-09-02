"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { AlertsTicker } from "@/components/alerts-ticker"
import { CommoditySignals } from "@/components/commodity-signals"
import { GeospatialMap } from "@/components/geospatial-map"
import { RegulatoryScanner } from "@/components/regulatory-scanner"
import { SignalsTimeline } from "@/components/signals-timeline"
import { mockSignals } from "@/lib/mock-data"

export default function VisasPage() {
  const [signals, setSignals] = useState([])
  const [selectedSignal, setSelectedSignal] = useState(null)

  useEffect(() => {
    // Filter signals for visa-related content
    const visaSignals = mockSignals.filter(
      (signal) =>
        signal.headline.toLowerCase().includes("visa") ||
        signal.headline.toLowerCase().includes("h-2a") ||
        signal.headline.toLowerCase().includes("h-2b") ||
        signal.headline.toLowerCase().includes("labor") ||
        signal.headline.toLowerCase().includes("worker") ||
        signal.headline.toLowerCase().includes("immigration") ||
        signal.headline.toLowerCase().includes("seasonal"),
    )
    setSignals(visaSignals)

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
