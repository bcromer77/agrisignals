"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  ArrowRight,
  TrendingUp,
  Globe,
  Eye,
  Brain,
  Smartphone,
  Beef,
  Coffee,
  Citrus,
  Leaf,
  Coins as Corn,
  Plane,
  Building2,
  Database,
  Filter,
  Share2,
} from "lucide-react"
import Link from "next/link"
import LiveFeed from "@/components/LiveFeed"

export default function LandingPage() {
  const [email, setEmail] = useState("")
  const [firm, setFirm] = useState("")
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [demoScene, setDemoScene] = useState(0)
  const [mapPulse, setMapPulse] = useState(0)
  const [showSignupModal, setShowSignupModal] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState("")

  useEffect(() => {
    const interval = setInterval(() => {
      setDemoScene((prev) => (prev + 1) % 6)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const pulseInterval = setInterval(() => {
      setMapPulse((prev) => (prev + 1) % 3)
    }, 1500)
    return () => clearInterval(pulseInterval)
  }, [])

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsSubmitted(true)
  }

  const handleCategoryClick = (category: string) => {
    setSelectedCategory(category)
    setShowSignupModal(true)
  }

  const signalCategories = [
    {
      icon: Beef,
      title: "Cattle Index",
      description: "Herd size, auctions, feedlots.",
      tags: ["Real-time", "USDA"],
      borderColor: "border-l-red-500",
      bgColor: "bg-red-50",
      category: "cattle",
    },
    {
      icon: Coffee,
      title: "Coffee Exports",
      description: "Brazil drought, futures.",
      tags: ["Futures", "NOAA"],
      borderColor: "border-l-amber-500",
      bgColor: "bg-amber-50",
      category: "coffee",
    },
    {
      icon: Citrus,
      title: "Citrus Outlook",
      description: "Greening, water rulings.",
      tags: ["Florida", "Water Rights"],
      borderColor: "border-l-orange-500",
      bgColor: "bg-orange-50",
      category: "citrus",
    },
    {
      icon: Leaf,
      title: "Cannabis Index",
      description: "DEA scheduling, state filings.",
      tags: ["DEA", "Policy"],
      borderColor: "border-l-green-500",
      bgColor: "bg-green-50",
      category: "cannabis",
    },
    {
      icon: Corn,
      title: "Corn & Policy",
      description: "Litigation, tariffs, bans.",
      tags: ["Regulatory", "Trade"],
      borderColor: "border-l-yellow-500",
      bgColor: "bg-yellow-50",
      category: "corn",
    },
    {
      icon: Plane,
      title: "Visa Applications",
      description: "H-2A approvals vs quarterly.",
      tags: ["USCIS", "Labor"],
      borderColor: "border-l-blue-500",
      bgColor: "bg-blue-50",
      category: "visa",
    },
    {
      icon: Building2,
      title: "Retail Exposure",
      description: "Supply risks with equities.",
      tags: ["Exposure", "Equity Risk"],
      borderColor: "border-l-purple-500",
      bgColor: "bg-purple-50",
      category: "exposure",
    },
  ]

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white flex items-center justify-center">
        <Card className="max-w-md w-full mx-4 bg-black/50 border-gray-800">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl text-white">Access Granted</CardTitle>
            <CardDescription className="text-gray-300">Welcome to the contrarian intelligence terminal</CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Link href="/dashboard">
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                Enter Dashboard <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-xl border-b border-gray-200">
        <div className="container mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            <div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                AGRISIGNALS
              </span>
              <div className="text-xs text-gray-500">PRISM</div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="hidden md:block text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              Powered by USDA, NOAA, USCIS
            </div>
            <nav className="hidden md:flex space-x-4 text-sm">
              <Link href="#pricing" className="text-gray-600 hover:text-blue-600 transition-colors">
                Pricing
              </Link>
              <Link href="/signup" className="text-gray-600 hover:text-blue-600 transition-colors">
                Signup
              </Link>
            </nav>
            <Button size="sm" className="bg-blue-500 hover:bg-blue-600 text-white">
              Get Started
            </Button>
          </div>
        </div>
      </header>

      <section className="py-16 relative bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="absolute inset-0 opacity-20">
          {/* Vegas water rationing - Red hotspot */}
          <div className="absolute top-1/3 left-1/4">
            <div
              className={`w-3 h-3 bg-red-500 rounded-full animate-ping ${mapPulse === 0 ? "opacity-100" : "opacity-50"}`}
            ></div>
          </div>
          {/* São Paulo - Green hotspot */}
          <div className="absolute top-2/3 left-1/2">
            <div
              className={`w-3 h-3 bg-green-500 rounded-full animate-ping ${mapPulse === 1 ? "opacity-100" : "opacity-50"}`}
            ></div>
          </div>
          {/* Oklahoma - Red hotspot */}
          <div className="absolute top-1/2 right-1/3">
            <div
              className={`w-3 h-3 bg-red-500 rounded-full animate-ping ${mapPulse === 2 ? "opacity-100" : "opacity-50"}`}
            ></div>
          </div>
        </div>

        <div className="container mx-auto px-6 relative text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 text-gray-900">
            Real-Time Agriculture & Supply Chain Signals.
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-4xl mx-auto">
            Live indices across cattle, coffee, citrus, labor, and regulatory filings — structured into dashboards and
            delivered via WhatsApp.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Button size="lg" className="bg-blue-500 hover:bg-blue-600 text-white px-8">
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-gray-300 text-gray-700 hover:bg-gray-50 px-8 bg-transparent"
            >
              Book a Demo
            </Button>
          </div>
          <div className="text-sm text-gray-500">Trusted by supply chain teams</div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-lg md:text-xl font-bold mb-2 text-gray-900">Explore Signal Categories</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {signalCategories.map((signal, index) => (
              <Card
                key={index}
                className={`bg-white border-l-4 ${signal.borderColor} hover:shadow-md transition-all cursor-pointer group`}
                onClick={() => handleCategoryClick(signal.category)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`w-10 h-10 ${signal.bgColor} rounded-lg flex items-center justify-center`}>
                      <signal.icon className="h-5 w-5 text-gray-700" />
                    </div>
                    <CardTitle className="text-base text-gray-900">{signal.title}</CardTitle>
                  </div>
                  <CardDescription className="text-base text-gray-600">{signal.description}</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-1 mb-3">
                    {signal.tags.map((tag, tagIndex) => (
                      <Badge key={tagIndex} variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <Button size="sm" className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700">
                    View Dashboard
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-lg md:text-xl font-bold mb-2 text-gray-900">How It Works</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Database className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">Ingest</h3>
              <p className="text-base text-gray-600">
                Auction barns, USCIS filings, NOAA drought indices, USDA reports.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Filter className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">Structure</h3>
              <p className="text-base text-gray-600">Signals cleaned into categories, confidence scores, provenance.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Share2 className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">Distribute</h3>
              <p className="text-base text-gray-600">Dashboards, WhatsApp alerts, API feeds.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-lg md:text-xl font-bold mb-2 text-gray-900">
              From raw events to structured signals — conviction in 60 seconds.
            </h2>
          </div>

          <div className="max-w-5xl mx-auto">
            <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-lg">
              <div className="relative h-80 overflow-hidden rounded-xl bg-gray-900">
                {/* Scene 3: Dashboard Comes Alive - Flashing Alerts */}
                <div
                  className={`absolute inset-0 transition-all duration-1000 ${demoScene === 0 ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-full"}`}
                >
                  <div className="p-6 h-full flex flex-col justify-center">
                    <div className="text-center mb-6">
                      <Eye className="h-12 w-12 text-red-400 mx-auto mb-3 animate-pulse" />
                      <h3 className="text-lg md:text-xl font-bold text-white mb-2">Flashing Alerts Ticker</h3>
                      <p className="text-base text-gray-400">Real-time anomaly detection across 10,000+ sources</p>
                    </div>
                    <div className="space-y-3">
                      <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3 animate-pulse">
                        <div className="flex items-center justify-between">
                          <span className="text-red-400 font-mono text-sm">🚨 Oklahoma cattle auction +14%</span>
                          <Badge className="bg-red-600 text-xs">URGENT</Badge>
                        </div>
                      </div>
                      <div
                        className="bg-blue-900/30 border border-blue-500/50 rounded-lg p-3 animate-pulse"
                        style={{ animationDelay: "0.5s" }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-blue-400 font-mono text-sm">💧 Vegas hotel water rationing risk ↑</span>
                          <Badge className="bg-blue-600 text-xs">HIGH</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scene 4: SignalCard Expansion - Who Bleeds vs Benefits */}
                <div
                  className={`absolute inset-0 transition-all duration-1000 ${demoScene === 1 ? "opacity-100 translate-x-0" : demoScene < 1 ? "opacity-0 translate-x-full" : "opacity-0 -translate-x-full"}`}
                >
                  <div className="p-6 h-full flex flex-col justify-center">
                    <div className="text-center mb-6">
                      <Brain className="h-12 w-12 text-purple-400 mx-auto mb-3" />
                      <h3 className="text-lg md:text-xl font-bold text-white mb-2">SignalCard Intelligence</h3>
                      <p className="text-base text-gray-400">Confidence: 82% | Edge: ~5 days</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3">
                        <div className="text-red-400 font-semibold mb-2 text-sm">WHO BLEEDS</div>
                        <div className="text-white text-sm">• Processors</div>
                        <div className="text-white text-sm">• Hotels</div>
                        <div className="text-white text-sm">• Restaurants</div>
                      </div>
                      <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-3">
                        <div className="text-green-400 font-semibold mb-2 text-sm">WHO BENEFITS</div>
                        <div className="text-white text-sm">• Exporters</div>
                        <div className="text-white text-sm">• Suppliers</div>
                        <div className="text-white text-sm">• Alternative Proteins</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scene 5: Geo-Map Zoom & Causal Radar (Rosling Style) */}
                <div
                  className={`absolute inset-0 transition-all duration-1000 ${demoScene === 2 ? "opacity-100 translate-x-0" : demoScene < 2 ? "opacity-0 translate-x-full" : "opacity-0 -translate-x-full"}`}
                >
                  <div className="p-6 h-full flex flex-col justify-center">
                    <div className="text-center mb-6">
                      <Globe className="h-12 w-12 text-green-400 mx-auto mb-3" />
                      <h3 className="text-lg md:text-xl font-bold text-white mb-2">Impact Radar</h3>
                      <p className="text-base text-gray-400">Causal flow analysis - Texas Panhandle glows red</p>
                    </div>
                    <div className="relative bg-gray-800 rounded-lg h-24 flex items-center justify-center">
                      <div className="absolute inset-0 bg-gradient-to-r from-red-900/20 via-orange-900/20 to-green-900/20 rounded-lg"></div>
                      <div className="relative flex space-x-6">
                        <div className="w-4 h-4 bg-red-500 rounded-full animate-ping"></div>
                        <div
                          className="w-3 h-3 bg-orange-500 rounded-full animate-ping"
                          style={{ animationDelay: "0.5s" }}
                        ></div>
                        <div
                          className="w-3 h-3 bg-yellow-500 rounded-full animate-ping"
                          style={{ animationDelay: "1s" }}
                        ></div>
                        <div
                          className="w-3 h-3 bg-green-500 rounded-full animate-ping"
                          style={{ animationDelay: "1.5s" }}
                        ></div>
                      </div>
                      <div className="absolute bottom-1 left-2 text-xs text-gray-400">
                        Bubble flows: Source → Outcome
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scene 6: WhatsApp Distribution */}
                <div
                  className={`absolute inset-0 transition-all duration-1000 ${demoScene === 3 ? "opacity-100 translate-x-0" : demoScene < 3 ? "opacity-0 translate-x-full" : "opacity-0 -translate-x-full"}`}
                >
                  <div className="p-6 h-full flex flex-col justify-center">
                    <div className="text-center mb-6">
                      <Smartphone className="h-12 w-12 text-green-400 mx-auto mb-3" />
                      <h3 className="text-lg md:text-xl font-bold text-white mb-2">WhatsApp Export</h3>
                      <p className="text-base text-gray-400">Signals distributed instantly via Twilio</p>
                    </div>
                    <div className="flex justify-center">
                      <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-3 max-w-sm">
                        <div className="text-green-400 font-semibold mb-2 text-sm">
                          🚨 Cattle auction prices +14% in Oklahoma
                        </div>
                        <div className="text-white text-sm">Confidence: 82% | Edge: ~5 days</div>
                        <div className="text-gray-400 text-xs mt-2">Provenance: USDA receipts</div>
                      </div>
                    </div>
                    <div className="text-center mt-4">
                      <Button size="sm" className="bg-green-600 hover:bg-green-700 animate-pulse">
                        📱 Share via WhatsApp
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Scene 7: The Inevitable Index - World Map Hotspots */}
                <div
                  className={`absolute inset-0 transition-all duration-1000 ${demoScene === 4 ? "opacity-100 translate-x-0" : demoScene < 4 ? "opacity-0 translate-x-full" : "opacity-0 -translate-x-full"}`}
                >
                  <div className="p-6 h-full flex flex-col justify-center">
                    <div className="text-center mb-6">
                      <TrendingUp className="h-12 w-12 text-yellow-400 mx-auto mb-3" />
                      <h3 className="text-lg md:text-xl font-bold text-white mb-2">Global Hotspots</h3>
                      <p className="text-base text-gray-400">Vegas • São Paulo • Los Angeles • Oklahoma • Beijing</p>
                    </div>
                    <div className="relative bg-gray-800 rounded-lg h-24 flex items-center justify-center">
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-900/20 via-purple-900/20 to-red-900/20 rounded-lg"></div>
                      <div className="relative grid grid-cols-5 gap-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        <div
                          className="w-2 h-2 bg-red-500 rounded-full animate-pulse"
                          style={{ animationDelay: "0.5s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"
                          style={{ animationDelay: "1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-green-500 rounded-full animate-pulse"
                          style={{ animationDelay: "1.5s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"
                          style={{ animationDelay: "2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scene 8: Closing Message */}
                <div
                  className={`absolute inset-0 transition-all duration-1000 ${demoScene === 5 ? "opacity-100 translate-x-0" : "opacity-0 translate-x-full"}`}
                >
                  <div className="p-6 h-full flex flex-col justify-center text-center">
                    <h3 className="text-2xl md:text-3xl font-bold text-white mb-3 leading-tight">
                      Bloomberg built the terminal
                      <br />
                      for Wall Street.
                    </h3>
                    <h3 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent mb-6 leading-tight">
                      We're building the terminal
                      <br />
                      for the real economy.
                    </h3>
                    <Button className="bg-blue-500 hover:bg-blue-600 text-white mx-auto animate-pulse">
                      Get Started
                    </Button>
                  </div>
                </div>

                {/* Progress indicator */}
                <div className="absolute bottom-3 left-1/2 transform -translate-x-1/2 flex space-x-2">
                  {[0, 1, 2, 3, 4, 5].map((scene) => (
                    <div
                      key={scene}
                      className={`w-2 h-2 rounded-full transition-all duration-300 ${
                        scene === demoScene ? "bg-blue-400 scale-125" : "bg-gray-600"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <LiveFeed />

      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-lg md:text-xl font-bold mb-2 text-gray-900">Use Cases</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">For Traders</h3>
              <p className="text-base text-gray-600">Spot anomalies before markets react.</p>
            </div>
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">For Producers</h3>
              <p className="text-base text-gray-600">Monitor labor + water risks affecting crops.</p>
            </div>
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">For Supply Chain Managers</h3>
              <p className="text-base text-gray-600">Track retail/wholesale exposure to commodities.</p>
            </div>
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg md:text-xl font-semibold mb-2 text-gray-900">For Consultants</h3>
              <p className="text-base text-gray-600">Benchmark risks for clients (HKA, Deloitte).</p>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-lg md:text-xl font-bold mb-2 text-gray-900">Pricing</h2>
            <p className="text-base text-gray-600">Simple & transparent</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Card className="bg-white border-gray-200 hover:shadow-md transition-all">
              <CardHeader className="text-center pb-3">
                <CardTitle className="text-base mb-2 text-gray-900">Starter</CardTitle>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  $99<span className="text-sm text-gray-500">/mo</span>
                </div>
                <CardDescription className="text-gray-600 text-sm">For retail traders & agri pros</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• 3 signals + weekly summary</li>
                </ul>
                <Button size="sm" className="w-full bg-gray-900 hover:bg-gray-800 text-white">
                  Get Started
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-white border-blue-500 hover:shadow-lg transition-all relative scale-105">
              <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              </div>
              <CardHeader className="text-center pb-3 pt-4">
                <CardTitle className="text-base mb-2 text-gray-900">Pro</CardTitle>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  $2k<span className="text-sm text-gray-500">/mo</span>
                </div>
                <CardDescription className="text-gray-600 text-sm">For funds & supply chain desks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Daily signals, dashboards, WhatsApp alerts</li>
                </ul>
                <Button size="sm" className="w-full bg-blue-500 hover:bg-blue-600 text-white">
                  Get Started
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-white border-gray-200 hover:shadow-md transition-all">
              <CardHeader className="text-center pb-3">
                <CardTitle className="text-base mb-2 text-gray-900">Enterprise</CardTitle>
                <div className="text-2xl font-bold text-gray-900 mb-1">Custom</div>
                <CardDescription className="text-gray-600 text-sm">For hedge funds/consultancies</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Unlimited signals, API feed, dedicated support</li>
                </ul>
                <Button size="sm" className="w-full bg-gray-900 hover:bg-gray-800 text-white">
                  Contact Sales
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-6xl font-bold mb-8 text-gray-900">
            Turn raw events into supply chain intelligence.
          </h2>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-blue-500 hover:bg-blue-600 text-white px-8">
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-gray-300 text-gray-700 hover:bg-gray-50 px-8 bg-transparent"
            >
              Book Demo with Our Team
            </Button>
          </div>
        </div>
      </section>

      <footer className="bg-gray-50 border-t border-gray-200 py-8">
        <div className="container mx-auto px-6">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xs">A</span>
              </div>
              <span className="font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                AGRISIGNALS
              </span>
            </div>
            <div className="flex space-x-4 text-sm text-gray-500">
              <Link href="#pricing" className="hover:text-blue-600">
                Pricing
              </Link>
              <Link href="/signup" className="hover:text-blue-600">
                Docs
              </Link>
              <Link href="#" className="hover:text-blue-600">
                Contact
              </Link>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6 text-center">
            <p className="text-sm text-gray-500 mb-2">
              Agrisignals PRISM is an intelligence and signaling platform. We do not provide investment advice.
            </p>
          </div>
        </div>
      </footer>

      {showSignupModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full bg-white">
            <CardHeader>
              <CardTitle className="text-xl text-gray-900">
                Unlock {selectedCategory.charAt(0).toUpperCase() + selectedCategory.slice(1)} Dashboard
              </CardTitle>
              <CardDescription className="text-gray-600">
                Sign up to access detailed signals and analytics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSignup} className="space-y-4">
                <div>
                  <input
                    type="email"
                    placeholder="Email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <input
                    type="text"
                    placeholder="Firm name"
                    value={firm}
                    onChange={(e) => setFirm(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div className="flex space-x-3">
                  <Button type="submit" className="flex-1 bg-blue-500 hover:bg-blue-600 text-white">
                    Get Access
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowSignupModal(false)}
                    className="flex-1 border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
