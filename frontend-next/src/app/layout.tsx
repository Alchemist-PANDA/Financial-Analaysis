import type { Metadata } from "next";
import "./globals.css";
import Script from "next/script";

export const metadata: Metadata = {
  title: "Apex Analytics | Institutional Terminal",
  description: "High-density financial analysis terminal for institutional equity research.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script src="https://s3.tradingview.com/tv.js" strategy="beforeInteractive" />
      </body>
    </html>
  );
}
