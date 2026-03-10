import type { Metadata } from "next";
import { JetBrains_Mono, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
});

export const metadata: Metadata = {
  title: "Dead Drop — The Stories That Fell Through the Cracks",
  description:
    "AI-powered intelligence, geopolitics, and cybersecurity analysis. Buried reports. Declassified files. Forgotten wars. Verified, sourced, no tinfoil.",
  keywords: [
    "intelligence",
    "geopolitics",
    "OSINT",
    "cybersecurity",
    "declassified",
    "military history",
    "AI",
    "newsletter",
  ],
  openGraph: {
    title: "Dead Drop — The Stories That Fell Through the Cracks",
    description:
      "AI-powered intelligence analysis. Buried reports. Declassified files. Forgotten wars.",
    type: "website",
    url: "https://dead-drop.co",
    siteName: "Dead Drop",
  },
  twitter: {
    card: "summary_large_image",
    site: "@DeadDropIntel",
    title: "Dead Drop — The Stories That Fell Through the Cracks",
    description:
      "AI-powered intelligence analysis. Buried reports. Declassified files. Forgotten wars.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
