import Link from "next/link";

export function TopBar() {
  return (
    <header className="topbar">
      <Link href="/" className="wordmark" aria-label="Sentinel, home">sentinel<span aria-hidden>_</span></Link>
      <nav aria-label="Main">
        <Link href="/#how">How it works</Link>
        <Link href="/#limits">Limits</Link>
      </nav>
    </header>
  );
}
