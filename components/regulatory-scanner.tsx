"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollText, Scale, FileText, AlertCircle } from "lucide-react"

interface Signal {
  id: number
  headline: string
  city: string
  state?: string
  commodity: string
  score: number
  so_what: string
  who_bleeds: string
  who_benefits: string
  signalStrength: string
}

interface RegulatoryScannerProps {
  signals: Signal[]
}

export function RegulatoryScanner({ signals }: RegulatoryScannerProps) {
  const regulatoryEvents = [
    { type: "lawsuit", title: "Colorado vs Nebraska water lawsuit", status: "active", risk: "high" },
    { type: "policy", title: "DEA cannabis reschedule risk", status: "pending", risk: "medium" },
    { type: "tariff", title: "Brazil beef tariffs increase", status: "enacted", risk: "high" },
    { type: "filing", title: "SGMA water rights filings", status: "review", risk: "low" },
  ]

  const riskHeatmap = signals.reduce(
    (acc, signal) => {
      const region = signal.state || "International"
      if (!acc[region]) acc[region] = []
      acc[region].push(signal.score)
      return acc
    },
    {} as Record<string, number[]>,
  )

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Regulatory Scanner */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <ScrollText className="h-5 w-5 text-primary" />
            <span className="text-foreground">Regulatory Scanner</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {regulatoryEvents.map((event, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 bg-muted/20 rounded border border-border/50"
            >
              <div className="flex items-center gap-2">
                {event.type === "lawsuit" && <Scale className="h-4 w-4 text-destructive" />}
                {event.type === "policy" && <FileText className="h-4 w-4 text-chart-2" />}
                {event.type === "tariff" && <AlertCircle className="h-4 w-4 text-destructive" />}
                {event.type === "filing" && <ScrollText className="h-4 w-4 text-muted-foreground" />}
                <div>
                  <p className="text-xs font-medium text-foreground">{event.title}</p>
                  <p className="text-xs text-muted-foreground">{event.status}</p>
                </div>
              </div>
              <Badge
                variant={event.risk === "high" ? "destructive" : event.risk === "medium" ? "secondary" : "outline"}
                className="text-xs"
              >
                {event.risk}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Emerging Risks Heatmap */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <span className="text-foreground">Emerging Risks</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(riskHeatmap).map(([region, scores]) => {
              const avgScore = scores.reduce((sum, score) => sum + score, 0) / scores.length
              return (
                <div
                  key={region}
                  className={`p-3 rounded text-center border ${
                    avgScore > 85
                      ? "bg-destructive/20 border-destructive/50"
                      : avgScore > 80
                        ? "bg-chart-2/20 border-chart-2/50"
                        : "bg-muted/20 border-border/50"
                  }`}
                >
                  <p className="text-xs font-medium text-foreground">{region}</p>
                  <p className="text-lg font-bold text-foreground">{avgScore.toFixed(0)}</p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Watchlist */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <span className="text-foreground">Your Watchlist</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {["Florida Citrus", "Vegas Tourism", "Brazil Coffee Exports", "US Cattle Futures"].map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 bg-muted/20 rounded border border-border/50"
            >
              <span className="text-sm text-foreground">{item}</span>
              <Badge variant="outline" className="text-xs">
                Tracking
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
