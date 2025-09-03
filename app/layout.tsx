import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriSignals | Real-Time Agriculture & Supply Chain Intelligence for Smarter Investments",
  description:
    "AgriSignals provides real-time intelligence on cattle, coffee, citrus, labor, and global commodities. Monitor supply chain disruptions, market shifts, hedge fund insights, and real-time signals.",
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

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
      <body className="bg-black font-sans">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

