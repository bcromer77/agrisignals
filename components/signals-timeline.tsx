"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, TrendingUp, Clock } from "lucide-react"

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

interface SignalsTimelineProps {
  signals: Signal[]
}

export function SignalsTimeline({ signals }: SignalsTimelineProps) {
  const timelineData = Array.from({ length: 7 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - i))
    const daySignals = signals.filter(() => Math.random() > 0.3)
    const avgScore = daySignals.length > 0 ? daySignals.reduce((sum, s) => sum + s.score, 0) / daySignals.length : 75

    return {
      date: date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }),
      signals: daySignals.length,
      avgScore: avgScore,
      trend: i > 0 ? (avgScore > 80 ? "up" : "down") : "neutral",
    }
  })

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <span className="text-foreground">Signals Timeline</span>
          <Badge variant="outline" className="ml-auto">
            7-Day View
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="flex items-end justify-between gap-2 h-24 mb-4">
          {timelineData.map((day, index) => (
            <div key={index} className="flex flex-col items-center gap-1 flex-1">
              <div
                className={`w-full rounded-t transition-all duration-300 ${
                  day.avgScore > 85 ? "bg-destructive" : day.avgScore > 80 ? "bg-chart-2" : "bg-primary"
                }`}
                style={{ height: `${(day.avgScore / 100) * 80}px` }}
              />
              <div className="flex items-center gap-1">
                {day.trend === "up" && <TrendingUp className="h-3 w-3 text-accent" />}
                {day.trend === "down" && <TrendingUp className="h-3 w-3 text-destructive rotate-180" />}
                <span className="text-xs text-muted-foreground">{day.date}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-destructive rounded" />
              <span className="text-xs text-muted-foreground">High Risk</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-chart-2 rounded" />
              <span className="text-xs text-muted-foreground">Medium</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-primary rounded" />
              <span className="text-xs text-muted-foreground">Normal</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
