"use client"

import { useState, useEffect } from "react"
import * as Tooltip from "@radix-ui/react-tooltip"

type Signal = {
  id: string
  headline: string
  confidence: number
  timestamp: string
  category: string
}

const sampleSignals: Signal[] = [
  {
    id: "sig-203",
    headline: "Cattle auction prices +14% in Oklahoma",
    confidence: 82,
    timestamp: "2025-08-26T13:20:00Z",
    category: "Cattle",
  },
  {
    id: "sig-312",
    headline: "H-2A visa approvals down 12% in California",
    confidence: 85,
    timestamp: "2025-08-26T12:05:00Z",
    category: "Labor",
  },
  {
    id: "sig-414",
    headline: "Citrus greening outbreak detected in Florida",
    confidence: 78,
    timestamp: "2025-08-25T16:45:00Z",
    category: "Citrus",
  },
  {
    id: "sig-509",
    headline: "RFK Jr. pushes litigation to ban corn syrup imports",
    confidence: 80,
    timestamp: "2025-08-25T14:10:00Z",
    category: "Regulatory",
  },
  {
    id: "sig-601",
    headline: "BJ's Wholesale flagged: 35% fresh produce exposure",
    confidence: 88,
    timestamp: "2025-08-24T09:15:00Z",
    category: "Retail",
  },
]

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export default function LiveFeed() {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadSignals = () => {
      setTimeout(() => {
        setSignals(sampleSignals)
        setLoading(false)
      }, 500) // Simulate loading delay
    }
    loadSignals()
  }, [])

  return (
    <section className="bg-gray-950 text-white py-12">
      <div className="max-w-5xl mx-auto px-6">
        <h2 className="text-3xl font-bold mb-6">Live Signal Preview</h2>
        <p className="text-gray-400 mb-8">
          A snapshot of current market disruptions. Unlock the full feed by creating an account.
        </p>

        {loading ? (
          <p className="text-gray-400">Loading signals...</p>
        ) : (
          <div className="space-y-4">
            {signals.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-900 px-4 py-3 hover:border-blue-400 transition"
              >
                <div>
                  <p className="font-medium">{s.headline}</p>
                  <p className="text-sm text-gray-400">
                    {s.category} · {formatTime(s.timestamp)}
                  </p>
                </div>

                <Tooltip.Provider>
                  <Tooltip.Root>
                    <Tooltip.Trigger asChild>
                      <span
                        className={`px-3 py-1 text-sm rounded-full cursor-help ${
                          s.confidence > 85 ? "bg-green-600/20 text-green-400" : "bg-yellow-600/20 text-yellow-400"
                        }`}
                      >
                        {s.confidence}% confidence
                      </span>
                    </Tooltip.Trigger>
                    <Tooltip.Content
                      side="top"
                      className="rounded bg-gray-800 text-gray-200 p-3 text-sm shadow-lg max-w-xs"
                    >
                      <p className="mb-1 font-semibold">Confidence Breakdown</p>
                      <ul className="list-disc ml-4 space-y-1 text-gray-400">
                        <li>Source Coverage (USDA, USCIS, NOAA corroboration)</li>
                        <li>Signal Strength (size vs quarterly baselines)</li>
                        <li>Model Certainty (rules + AI ensemble)</li>
                      </ul>
                      <Tooltip.Arrow className="fill-gray-800" />
                    </Tooltip.Content>
                  </Tooltip.Root>
                </Tooltip.Provider>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 text-center">
          <a
            href="/signup"
            className="px-6 py-3 rounded-lg bg-blue-500 hover:bg-blue-600 font-semibold text-white transition"
          >
            Unlock Full Feed
          </a>
        </div>
      </div>
    </section>
  )
}
