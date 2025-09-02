"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  LayoutDashboard,
  Coffee,
  Beef,
  Wheat,
  Leaf,
  Triangle as Orange,
  Scale,
  Menu,
  X,
  Building2,
  FileText,
  Activity,
} from "lucide-react"
import { cn } from "@/lib/utils"

const categories = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, color: "blue", count: 24 },
  { name: "Cities", href: "/cities", icon: Building2, color: "green", count: 8 },
  { name: "Coffee", href: "/coffee", icon: Coffee, color: "amber", count: 12 },
  { name: "Cannabis", href: "/cannabis", icon: Leaf, color: "emerald", count: 6 },
  { name: "Corn", href: "/corn", icon: Wheat, color: "yellow", count: 15 },
  { name: "Cattle", href: "/cattle", icon: Beef, color: "red", count: 9 },
  { name: "Citrus", href: "/citrus", icon: Orange, color: "orange", count: 4 },
  { name: "Regulatory", href: "/regulatory", icon: Scale, color: "purple", count: 18 },
  { name: "Visas", href: "/visas", icon: FileText, color: "indigo", count: 7 },
  { name: "Cracks", href: "/cracks", icon: Activity, color: "pink", count: 11 },
]

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const getColorClasses = (color: string, isActive: boolean) => {
    if (isActive) {
      const activeColors = {
        blue: "bg-blue-600 text-white hover:bg-blue-700 border-blue-600",
        green: "bg-green-600 text-white hover:bg-green-700 border-green-600",
        amber: "bg-amber-600 text-white hover:bg-amber-700 border-amber-600",
        emerald: "bg-emerald-600 text-white hover:bg-emerald-700 border-emerald-600",
        yellow: "bg-yellow-600 text-white hover:bg-yellow-700 border-yellow-600",
        red: "bg-red-600 text-white hover:bg-red-700 border-red-600",
        orange: "bg-orange-600 text-white hover:bg-orange-700 border-orange-600",
        purple: "bg-purple-600 text-white hover:bg-purple-700 border-purple-600",
        indigo: "bg-indigo-600 text-white hover:bg-indigo-700 border-indigo-600",
        pink: "bg-pink-600 text-white hover:bg-pink-700 border-pink-600",
      }
      return activeColors[color as keyof typeof activeColors] || activeColors.blue
    } else {
      const inactiveColors = {
        blue: "text-blue-700 hover:bg-blue-50 border-blue-200",
        green: "text-green-700 hover:bg-green-50 border-green-200",
        amber: "text-amber-700 hover:bg-amber-50 border-amber-200",
        emerald: "text-emerald-700 hover:bg-emerald-50 border-emerald-200",
        yellow: "text-yellow-700 hover:bg-yellow-50 border-yellow-200",
        red: "text-red-700 hover:bg-red-50 border-red-200",
        orange: "text-orange-700 hover:bg-orange-50 border-orange-200",
        purple: "text-purple-700 hover:bg-purple-50 border-purple-200",
        indigo: "text-indigo-700 hover:bg-indigo-50 border-indigo-200",
        pink: "text-pink-700 hover:bg-pink-50 border-pink-200",
      }
      return inactiveColors[color as keyof typeof inactiveColors] || inactiveColors.blue
    }
  }

  return (
    <>
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-lg">A</span>
                </div>
                <div>
                  <span className="text-2xl font-bold text-gray-900">AGRISIGNALS</span>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-xs text-gray-600 font-medium">LIVE TERMINAL</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="hidden md:flex items-center gap-4">
              <Badge className="bg-green-100 text-green-800 border-green-200">🟢 Markets Open</Badge>
              <Badge className="bg-blue-100 text-blue-800 border-blue-200">📊 114 Signals Active</Badge>
              <Link href="/pricing">
                <Button variant="ghost" size="sm" className="text-gray-700 hover:text-gray-900">
                  Pricing
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
                  Sign Up
                </Button>
              </Link>
            </div>

            <Button variant="ghost" size="sm" className="md:hidden" onClick={() => setIsOpen(!isOpen)}>
              {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </header>

      <nav className={cn("bg-white border-b border-gray-200 shadow-sm", isOpen ? "block" : "hidden md:block")}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-wrap items-center gap-2 py-4">
            {categories.map((category) => {
              const Icon = category.icon
              const isActive = pathname === category.href

              return (
                <Link key={category.name} href={category.href}>
                  <Button
                    variant="outline"
                    size="sm"
                    className={cn(
                      "flex items-center space-x-2 text-sm font-medium border-2 transition-all duration-200 hover:scale-105",
                      getColorClasses(category.color, isActive),
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{category.name}</span>
                    <Badge
                      variant="secondary"
                      className={cn(
                        "ml-1 text-xs px-1.5 py-0.5",
                        isActive
                          ? "bg-white/20 text-white border-white/30"
                          : "bg-gray-100 text-gray-600 border-gray-200",
                      )}
                    >
                      {category.count}
                    </Badge>
                  </Button>
                </Link>
              )
            })}

            <div className="md:hidden w-full flex gap-2 mt-2 pt-2 border-t border-gray-200">
              <Link href="/pricing" className="flex-1">
                <Button variant="outline" size="sm" className="w-full bg-transparent">
                  Pricing
                </Button>
              </Link>
              <Link href="/signup" className="flex-1">
                <Button size="sm" className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                  Sign Up
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>
    </>
  )
}
