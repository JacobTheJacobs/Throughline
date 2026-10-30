import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Throughline — Follow what connects",
    template: "%s · Throughline",
  },
  description: "Start with what you love and follow verified cultural connections across films, books, music, people, places, games, and brands.",
  applicationName: "Throughline",
  openGraph: {
    title: "Throughline — Follow what connects",
    description: "Start with what you love. See where the connections lead.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Throughline — Follow what connects",
    description: "Start with what you love. See where the connections lead.",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="dns-prefetch" href="//images.qloo.com" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
