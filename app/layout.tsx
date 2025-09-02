import type React from "react"
import type { Metadata } from "next"
import { Inter, JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
export const metadata = {
  title: "AgriSignals | Real-Time Agriculture & Supply Chain Intelligence for Smarter Investments",
  description:
    "AgriSignals provides real-time intelligence on cattle, coffee, citrus, labor, and global commodities. Monitor supply chain disruptions, market shifts, and regulatory changes — powered by AI analytics for hedge funds, traders, and agribusiness leaders.",
  keywords: [
    "agriculture data",
    "supply chain intelligence",
    "commodity analytics",
    "hedge fund insights",
    "AI in agriculture",
    "real-time market signals",
  ],
  openGraph: {
    title: "AgriSignals | Real-Time Agriculture & Supply Chain Intelligence",
    description:
      "AI-powered agriculture and supply chain dashboards delivering commodity intelligence for hedge funds, traders, and agribusiness leaders.",
    url: "https://agrisignals.com",
    siteName: "AgriSignals",
    images: [
      {
        url: "/placeholder-logo.png",
        width: 1200,
        height: 630,
        alt: "AgriSignals Dashboard",
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AgriSignals | Real-Time Agriculture & Supply Chain Intelligence",
    description:
      "AI-powered agriculture & supply chain dashboards for hedge funds, traders, and agribusiness leaders.",
    images: ["/placeholder-logo.png"],
  },
};
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
})

export const metadata: Metadata = {
  title: "Agrisignals - Commodity Intelligence Terminal",
  description: "Real-time commodity disruptions transformed into signal intelligence",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
      <head>
        <style>{`
html {
  font-family: var(--font-inter);
  --font-sans: var(--font-inter);
  --font-mono: var(--font-jetbrains-mono);
}
        `}</style>
      </head>
      <body className="bg-black font-sans">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
