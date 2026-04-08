import type { Metadata } from "next";
import "./globals.css";

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
      </body>
    </html>
  );
}
