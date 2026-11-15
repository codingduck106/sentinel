import type { Metadata } from "next";
import { TopBar } from "@/components/TopBar";
import { CheckClient } from "./CheckClient";

export const metadata: Metadata = {
  title: "Check a message — Veritas",
  description: "Paste a text message to see if it looks like a scam and which pressure tactics it uses.",
};

export default function CheckPage() {
  return (
    <div className="frame">
      <TopBar showCta={false} />
      <main className="check">
        <CheckClient />
      </main>
    </div>
  );
}
