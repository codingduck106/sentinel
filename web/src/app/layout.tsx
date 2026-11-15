import type { Metadata, Viewport } from "next";
import { Atkinson_Hyperlegible, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "700", "800"] });
const atkinson = Atkinson_Hyperlegible({ variable: "--font-atkinson", subsets: ["latin"], weight: ["400", "700"] });

export const metadata: Metadata = {
  title: "Sentinel — Scam text checker",
  description: "Check if a text message is a scam. Paste it and Sentinel flags the exact words trying to rush, scare or bribe you, gives a risk level, and tells you what to do next.",
};

export const viewport: Viewport = {
  themeColor: "#040705",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${mono.variable} ${atkinson.variable}`}>
      <body>{children}</body>
    </html>
  );
}
