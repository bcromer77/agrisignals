"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, Zap, Droplets, Wheat, Coffee } from "lucide-react"

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

interface CommoditySignalsProps {
  signals: Signal[]
  onSignalSelect: (signal: Signal) => void
  selectedSignal: Signal | null
}

const commodityIcons = {
  cattle: Wheat,
  water: Droplets,
  labor: TrendingUp,
  retail: TrendingDown,
  coffee: Coffee,
}

export function CommoditySignals({ signals, onSignalSelect, selectedSignal }: CommoditySignalsProps) {
  const commodityGroups = signals.reduce(
    (acc, signal) => {
      if (!acc[signal.commodity]) {
        acc[signal.commodity] = []
      }
      acc[signal.commodity].push(signal)
      return acc
    },
    {} as Record<string, Signal[]>,
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-bold text-foreground">COMMODITY SIGNALS</h2>
      </div>

      {Object.entries(commodityGroups).map(([commodity, commoditySignals]) => {
        const Icon = commodityIcons[commodity as keyof typeof commodityIcons] || Wheat
        const avgScore = commoditySignals.reduce((sum, s) => sum + s.score, 0) / commoditySignals.length

        return (
          <Card key={commodity} className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-primary" />
                  <span className="capitalize text-foreground">{commodity}</span>
                </div>
                <Badge variant={avgScore > 85 ? "destructive" : "secondary"} className="font-mono">
                  {avgScore.toFixed(0)}
                </Badge>
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-2">
              {commoditySignals.map((signal) => (
                <Button
                  key={signal.id}
                  variant={selectedSignal?.id === signal.id ? "default" : "ghost"}
                  className="w-full justify-start p-3 h-auto"
                  onClick={() => onSignalSelect(signal)}
                >
                  <div className="text-left">
                    <p className="text-sm font-medium text-foreground">{signal.headline}</p>
                    <p className="text-xs text-muted-foreground mt-1">{signal.so_what}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-xs">
                        {signal.city}
                        {signal.state && `, ${signal.state}`}
                      </Badge>
                      <Badge variant={signal.score > 85 ? "destructive" : "secondary"} className="text-xs font-mono">
                        {signal.score.toFixed(0)}
                      </Badge>
                    </div>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
