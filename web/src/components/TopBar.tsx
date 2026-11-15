import Link from "next/link";

export function TopBar({ showCta = true }: { showCta?: boolean }) {
  return (
    <header className="topbar">
      <Link href="/" className="wordmark">Veritas</Link>
      {showCta && <Link href="/check" className="btn btn-sm">Check a message</Link>}
    </header>
  );
}
