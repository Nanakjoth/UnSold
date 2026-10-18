import { useEffect, useState } from "react";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { listMentors } from "../services/advice";
import { ApiRequestError } from "../services/api";
import type { MentorCard } from "../types/api";

/** The controlled domain vocabulary shared with the matching engine. */
const DOMAINS = [
  "software",
  "data",
  "design",
  "product",
  "people-management",
  "career",
  "money",
  "business",
  "wellbeing",
  "research",
  "education",
  "nonprofit",
  "operations",
  "security",
  "trades",
];

function MentorTile({ mentor }: { mentor: MentorCard }) {
  const card = mentor.public_card;
  return (
    <article className="card-raised flex flex-col rounded-2xl border border-line bg-card p-5">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-ink-soft">{card.role_band}</p>
          <h3 className="mt-0.5 font-semibold">{mentor.pseudonym}</h3>
        </div>
        <span className="shrink-0 rounded-full bg-paper-deep px-2 py-0.5 text-[11px] text-ink-soft">
          {card.seniority_band}
        </span>
      </div>
      <p className="mt-2.5 flex-1 text-sm text-ink-soft">{card.bio_public}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {card.topics_offered.slice(0, 3).map((topic) => (
          <span key={topic} className="rounded-md bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-accent-strong">
            {topic}
          </span>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-line pt-3 text-[11px] text-ink-soft">
        {card.languages.map((lang) => (
          <span key={lang} className="rounded-md bg-paper-deep px-2 py-0.5">
            {lang}
          </span>
        ))}
        <span>{card.country_code}</span>
        {mentor.is_synthetic && <span className="ml-auto">Synthetic mentor</span>}
      </div>
    </article>
  );
}

export default function Mentors() {
  const [domain, setDomain] = useState("");
  const [items, setItems] = useState<MentorCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    listMentors({ domain: domain || undefined, limit: 60 })
      .then((response) => {
        if (!active) return;
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((err) => {
        if (!active) return;
        setError(
          err instanceof ApiRequestError
            ? err.message
            : "The directory could not be loaded. Check that the API is running.",
        );
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [domain]);

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight">People ready to help</h1>
          <p className="mt-2 text-ink-soft">
            {total} experienced peers across technical and non-technical fields.
            Every profile is synthetic for this prototype. Browse openly — no
            account needed.
          </p>
          <p className="mt-3 rounded-xl bg-paper px-4 py-3 text-xs text-ink-soft">
            Prefer to be matched instead of browsing?{" "}
            <a href="/" className="font-medium text-accent underline underline-offset-4">
              Describe your situation
            </a>{" "}
            and see the closest fits.
          </p>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          <button
            onClick={() => setDomain("")}
            aria-pressed={!domain}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
              !domain ? "border-accent bg-accent text-white" : "border-line-strong text-ink hover:border-accent hover:text-accent"
            }`}
          >
            All
          </button>
          {DOMAINS.map((d) => (
            <button
              key={d}
              onClick={() => setDomain(d)}
              aria-pressed={domain === d}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
                domain === d ? "border-accent bg-accent text-white" : "border-line-strong text-ink hover:border-accent hover:text-accent"
              }`}
            >
              {d.replace(/-/g, " ")}
            </button>
          ))}
        </div>

        {error && (
          <div role="alert" className="mt-5 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
            {error}
          </div>
        )}

        {loading && (
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-52 animate-pulse rounded-2xl border border-line bg-card" />
            ))}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="mt-8 rounded-2xl border border-dashed border-line-strong bg-card p-10 text-center">
            <p className="font-semibold">No mentors in that area yet.</p>
            <p className="mt-1 text-sm text-ink-soft">Try another area, or clear the filter.</p>
          </div>
        )}

        {!loading && items.length > 0 && (
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((mentor) => (
              <MentorTile key={mentor.id} mentor={mentor} />
            ))}
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
