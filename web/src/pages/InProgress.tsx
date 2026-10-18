import { Link } from "react-router-dom";
import { InnerHeader, SiteFooter } from "../components/Shell";

interface Props {
  title: string;
  detail: string;
}

/** Honest placeholder for screens that arrive in a later stage. */
export default function InProgress({ title, detail }: Props) {
  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />

      <main className="hero-wash flex-1">
        <div className="mx-auto max-w-2xl px-4 py-20">
          <div className="card-raised rounded-2xl border border-line bg-card p-8 sm:p-10">
            <span className="inline-flex items-center gap-2 rounded-full bg-warm-soft px-3 py-1 text-xs font-semibold text-warm">
              Arriving in a later stage
            </span>
            <h1 className="mt-4 text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-4 text-ink-soft">{detail}</p>
            <p className="mt-4 text-ink-soft">
              The product is built stage by stage so every stage leaves a working
              product. Nothing is mocked here — this screen simply is not built yet.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/"
                className="inline-flex min-h-11 items-center justify-center rounded-lg bg-accent px-5 py-2.5 font-medium text-white transition-colors hover:bg-accent-strong"
              >
                Back to the landing page
              </Link>
              <a
                href="/healthz"
                className="inline-flex min-h-11 items-center justify-center rounded-lg border border-line-strong px-5 py-2.5 font-medium text-ink transition-colors hover:border-accent hover:text-accent"
              >
                Check system health
              </a>
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
