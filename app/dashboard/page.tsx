"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { generateLiveSignals, type LiveSignal } from "@/lib/live-data"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { RefreshCw, TrendingUp, TrendingDown } from "lucide-react"

export default function Dashboard() {
  const [signals, setSignals] = useState<LiveSignal[]>([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState("6months")
  const [region, setRegion] = useState("all")
  const [showActivist, setShowActivist] = useState(true)
  const [showPredictive, setShowPredictive] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    loadLiveData()
    const interval = setInterval(loadLiveData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadLiveData = async () => {
    try {
      setLoading(true)
      const liveSignals = await generateLiveSignals()
      setSignals(liveSignals)
      setLastUpdate(new Date())
    } catch (error) {
      console.error("[v0] Failed to load live data:", error)
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = (price?: number) => {
    if (!price) return "N/A"
    return `$${price.toFixed(2)}`
  }

  const formatChange = (change?: number, changePercent?: number) => {
    if (change === undefined || changePercent === undefined) return null
    const isPositive = change >= 0
    return (
      <div className={`flex items-center gap-1 text-sm ${isPositive ? "text-green-600" : "text-red-600"}`}>
        {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        {isPositive ? "+" : ""}
        {change.toFixed(2)} ({isPositive ? "+" : ""}
        {changePercent.toFixed(1)}%)
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      {/* Enhanced Header Section */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="text-center mb-2">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Agrisignals Intelligence Terminal</h1>
            <p className="text-lg text-gray-600">
              Real-time commodity disruptions transformed into signal intelligence
            </p>
          </div>

          <div className="flex justify-center items-center gap-6 mt-8">
            <Badge className="bg-green-100 text-green-800 border-green-200 px-4 py-2 text-sm font-medium">
              🟢 Live Market Data
            </Badge>
            <Badge className="bg-blue-100 text-blue-800 border-blue-200 px-4 py-2 text-sm font-medium">
              📊 {signals.length} Active Signals
            </Badge>
            <Badge className="bg-orange-100 text-orange-800 border-orange-200 px-4 py-2 text-sm font-medium">
              ⚡ Last Update: {lastUpdate.toLocaleTimeString()}
            </Badge>
            <Button
              onClick={loadLiveData}
              disabled={loading}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 bg-transparent"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Simplified Controls Section */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-4 h-4 bg-blue-500 rounded-sm"></div>
            <h2 className="text-xl font-semibold text-gray-900">Risk Analysis Controls</h2>
          </div>
          <p className="text-gray-600 mb-6">Configure dashboard display and analysis parameters</p>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">Risk Types</Label>
              <Select value="all">
                <SelectTrigger className="w-full bg-white">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="commodity">Commodity</SelectItem>
                  <SelectItem value="regulatory">Regulatory</SelectItem>
                  <SelectItem value="weather">Weather</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger className="w-full bg-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="6months">Last 6 Months</SelectItem>
                  <SelectItem value="1year">Last Year</SelectItem>
                  <SelectItem value="2years">Last 2 Years</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">Region</Label>
              <Select value={region} onValueChange={setRegion}>
                <SelectTrigger className="w-full bg-white">
                  <SelectValue placeholder="All Regions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Regions</SelectItem>
                  <SelectItem value="north-america">North America</SelectItem>
                  <SelectItem value="south-america">South America</SelectItem>
                  <SelectItem value="europe">Europe</SelectItem>
                  <SelectItem value="asia">Asia</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">Risk Threshold: High</Label>
              <div className="w-full bg-gray-200 rounded-full h-3 mt-2">
                <div className="bg-red-500 h-3 rounded-full transition-all duration-300" style={{ width: "75%" }}></div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-8 mt-6">
            <div className="flex items-center space-x-3">
              <Switch id="activist" checked={showActivist} onCheckedChange={setShowActivist} />
              <Label htmlFor="activist" className="text-sm font-medium">
                Show Activist Layer
              </Label>
            </div>
            <div className="flex items-center space-x-3">
              <Switch id="predictive" checked={showPredictive} onCheckedChange={setShowPredictive} />
              <Label htmlFor="predictive" className="text-sm font-medium">
                Predictive Analytics
              </Label>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Live Signals Grid */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Live Market Signals</h2>
          <p className="text-gray-600">Real-time commodity disruptions with actionable intelligence</p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            <span className="ml-3 text-lg text-gray-600">Loading live market data...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {signals.map((signal) => (
              <Card
                key={signal.id}
                className={`border-l-4 shadow-lg hover:shadow-xl transition-shadow bg-white ${
                  signal.commodity === "coffee"
                    ? "border-l-amber-500"
                    : signal.commodity === "cattle"
                      ? "border-l-red-500"
                      : signal.commodity === "corn"
                        ? "border-l-yellow-500"
                        : signal.commodity === "water"
                          ? "border-l-blue-500"
                          : signal.commodity === "labor"
                            ? "border-l-purple-500"
                            : "border-l-gray-500"
                }`}
              >
                <CardHeader className="pb-4">
                  <div className="flex justify-between items-start mb-3">
                    <Badge
                      className={`px-3 py-1 text-xs font-medium ${
                        signal.score >= 90
                          ? "bg-red-50 text-red-700 border border-red-200"
                          : signal.score >= 80
                            ? "bg-orange-50 text-orange-700 border border-orange-200"
                            : "bg-yellow-50 text-yellow-700 border border-yellow-200"
                      }`}
                    >
                      Risk Score: {signal.score}
                    </Badge>
                    <Badge
                      variant="secondary"
                      className={`capitalize font-medium ${
                        signal.commodity === "coffee"
                          ? "bg-amber-100 text-amber-800 border-amber-200"
                          : signal.commodity === "cattle"
                            ? "bg-red-100 text-red-800 border-red-200"
                            : signal.commodity === "corn"
                              ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                              : signal.commodity === "water"
                                ? "bg-blue-100 text-blue-800 border-blue-200"
                                : signal.commodity === "labor"
                                  ? "bg-purple-100 text-purple-800 border-purple-200"
                                  : "bg-gray-100 text-gray-800 border-gray-200"
                      }`}
                    >
                      {signal.commodity}
                    </Badge>
                  </div>

                  <CardTitle className="text-lg font-bold text-gray-900 leading-tight mb-2">
                    {signal.headline}
                  </CardTitle>

                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>
                      📍 {signal.city}
                      {signal.state ? `, ${signal.state}` : ""}
                      {signal.country ? `, ${signal.country}` : ""}
                    </span>
                    {signal.price && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{formatPrice(signal.price)}</span>
                        {formatChange(signal.change, signal.changePercent)}
                      </div>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-1">💡 So What?</h4>
                      <p className="text-sm text-gray-700">{signal.so_what}</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <h4 className="font-semibold text-red-700 mb-1">🩸 Who Bleeds</h4>
                        <p className="text-sm text-gray-700">{signal.who_bleeds}</p>
                      </div>

                      <div>
                        <h4 className="font-semibold text-green-700 mb-1">💰 Who Benefits</h4>
                        <p className="text-sm text-gray-700">{signal.who_benefits}</p>
                      </div>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <h4 className="font-semibold text-slate-900 mb-1">🎯 Signal Strength</h4>
                      <p className="text-sm text-slate-700 font-medium">{signal.signalStrength}</p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center pt-3 border-t border-gray-200">
                    <span className="text-xs text-gray-500">
                      Source: {signal.source} • {new Date(signal.timestamp).toLocaleString()}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-green-600 border-green-200 hover:bg-green-50 bg-transparent"
                      >
                        📱 WhatsApp
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-purple-600 border-purple-200 hover:bg-purple-50 bg-transparent"
                      >
                        💬 Slack
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Compliance Footer */}
      <footer className="bg-white border-t py-6">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm text-gray-600">
            Agrisignals PRISM is an intelligence and signaling platform. We provide structured signals and anomalies
            from public data sources. We do not provide investment advice or execution services.
          </p>
        </div>
      </footer>
    </div>
  )
}
