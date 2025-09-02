"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MapPin, Globe, AlertTriangle, TrendingUp } from "lucide-react"

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

interface GeospatialMapProps {
  signals: Signal[]
  selectedSignal: Signal | null
  onSignalSelect: (signal: Signal) => void
}

export function GeospatialMap({ signals, selectedSignal, onSignalSelect }: GeospatialMapProps) {
  const riskZones = signals.filter((s) => s.score > 85)
  const opportunityZones = signals.filter((s) => s.score <= 85)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Globe className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-bold text-foreground">WATER & INFRASTRUCTURE</h2>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="text-foreground">Geospatial Stress Zones</span>
            <div className="flex gap-2">
              <Badge variant="destructive" className="text-xs">
                {riskZones.length} Risk
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {opportunityZones.length} Opportunity
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>

        <CardContent>
          <div className="relative bg-muted/10 rounded-lg p-6 min-h-[300px] border border-border/50">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 rounded-lg" />

            {/* Risk zones (red markers) */}
            {riskZones.map((signal, index) => (
              <Button
                key={signal.id}
                variant={selectedSignal?.id === signal.id ? "default" : "ghost"}
                size="sm"
                className={`absolute animate-pulse-glow ${
                  index === 0 ? "top-1/4 left-1/3" : index === 1 ? "top-1/2 right-1/4" : "bottom-1/3 left-1/2"
                }`}
                onClick={() => onSignalSelect(signal)}
              >
                <AlertTriangle className="h-4 w-4 text-destructive mr-1" />
                <span className="text-xs">{signal.city}</span>
              </Button>
            ))}

            {/* Opportunity zones (green markers) */}
            {opportunityZones.map((signal, index) => (
              <Button
                key={signal.id}
                variant={selectedSignal?.id === signal.id ? "default" : "ghost"}
                size="sm"
                className={`absolute ${index === 0 ? "top-1/3 right-1/3" : "bottom-1/4 left-1/4"}`}
                onClick={() => onSignalSelect(signal)}
              >
                <TrendingUp className="h-4 w-4 text-accent mr-1" />
                <span className="text-xs">{signal.city}</span>
              </Button>
            ))}

            <div className="absolute bottom-2 left-2 text-xs text-muted-foreground">Live Infrastructure Monitoring</div>
          </div>

          {/* Selected signal details */}
          {selectedSignal && (
            <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-border/50">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-primary" />
                  <span className="font-medium text-foreground">
                    {selectedSignal.city}
                    {selectedSignal.state && `, ${selectedSignal.state}`}
                  </span>
                </div>
                <Badge variant={selectedSignal.score > 85 ? "destructive" : "secondary"} className="font-mono">
                  {selectedSignal.score.toFixed(0)}
                </Badge>
              </div>

              <p className="text-sm text-foreground mb-3">{selectedSignal.headline}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-muted-foreground mb-1">Who Bleeds:</p>
                  <p className="text-destructive">{selectedSignal.who_bleeds}</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">Who Benefits:</p>
                  <p className="text-accent">{selectedSignal.who_benefits}</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-border/50">
                <p className="text-muted-foreground text-xs mb-1">Signal Strength:</p>
                <p className="text-sm font-medium text-primary">{selectedSignal.signalStrength}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
