"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, AlertTriangle } from "lucide-react"

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

interface AlertsTickerProps {
  signals: Signal[]
}

export function AlertsTicker({ signals }: AlertsTickerProps) {
  const topAlerts = signals.filter((s) => s.score > 85).slice(0, 3)

  return (
    <Card className="p-4 bg-card border-border">
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle className="h-5 w-5 text-destructive animate-flash" />
        <h2 className="text-lg font-bold text-foreground">LIVE ALERTS</h2>
        <Badge variant="destructive" className="animate-pulse-glow">
          {topAlerts.length} ACTIVE
        </Badge>
      </div>

      <div className="space-y-2">
        {topAlerts.map((signal) => (
          <div
            key={signal.id}
            className="flex items-center justify-between p-3 bg-muted/20 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              {signal.score > 90 ? (
                <TrendingUp className="h-4 w-4 text-destructive animate-flash" />
              ) : (
                <TrendingDown className="h-4 w-4 text-chart-2" />
              )}
              <div>
                <p className="text-sm font-medium text-foreground">{signal.headline}</p>
                <p className="text-xs text-muted-foreground">
                  {signal.city}
                  {signal.state && `, ${signal.state}`} • {signal.commodity}
                </p>
              </div>
            </div>

            <div className="text-right">
              <Badge variant={signal.score > 90 ? "destructive" : "secondary"} className="font-mono">
                {signal.score.toFixed(0)}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
