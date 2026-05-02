import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Canary — Can language in 10-K filings flag accounting fraud?",
  description:
    "A pre-registered study testing whether a single unsupervised signal over the language of SEC 10-K annual reports can flag historical accounting fraud — eight months before discovery, in five of six famous cases.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-page text-ink antialiased">
        {/* Top accent bar — institutional cue */}
        <div className="h-1 bg-navy-700" />

        <header className="bg-surface border-b border-rule">
          <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-baseline gap-2.5">
              <span className="font-serif text-[1.6rem] leading-none font-semibold text-navy-900 tracking-tightish">
                Canary
              </span>
              <span className="text-[10px] uppercase tracking-[0.18em] text-ink-3 font-medium pb-0.5 hidden sm:inline">
                A 10-K reading experiment
              </span>
            </Link>
            <nav className="flex items-center gap-6 text-[13px] font-medium text-ink-2">
              <Link href="/scan/" className="hover:text-navy-700 transition-colors">
                Scan a filing
              </Link>
              <Link href="/results/" className="hover:text-navy-700 transition-colors">
                Results
              </Link>
              <Link href="/baseline/" className="hover:text-navy-700 transition-colors">
                Baseline check
              </Link>
              <Link href="/methodology/" className="hover:text-navy-700 transition-colors">
                Methodology
              </Link>
              <Link href="/limitations/" className="hover:text-navy-700 transition-colors">
                Limitations
              </Link>
              <a
                href="https://github.com/ArseniiChan/canary"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-navy-700 transition-colors"
              >
                Source
              </a>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-12 md:py-16">{children}</main>

        <footer className="border-t border-rule mt-24 bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-8 flex flex-col md:flex-row md:items-baseline gap-3 md:justify-between text-xs text-ink-3">
            <div>
              CSC&nbsp;44800 (Artificial Intelligence) &middot; City College of New York,
              Spring 2026 &middot; Arsenii Chan &middot; Advisor: Prof. Erik K. Grimmelmann
            </div>
            <div>
              Spec frozen at git tag{" "}
              <span className="num">validation-spec-frozen</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
