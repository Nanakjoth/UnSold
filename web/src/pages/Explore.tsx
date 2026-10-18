import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import InterestCard from "../components/InterestCard";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { listCategories, listInterests } from "../services/catalogue";
import type { CategoryCount, InterestCard as InterestCardType } from "../types/api";
import { ApiRequestError } from "../services/api";

const PAGE_SIZE = 24;

const MODE_OPTIONS = [
  { value: "", label: "Any format" },
  { value: "solo", label: "Solo" },
  { value: "group", label: "Group" },
  { value: "online", label: "Online" },
  { value: "in_person", label: "In person" },
];

export default function Explore() {
  const [searchParams, setSearchParams] = useSearchParams();

  const q = searchParams.get("q") ?? "";
  const category = searchParams.get("category") ?? "";
  const mode = searchParams.get("mode") ?? "";
  const beginner = searchParams.get("beginner") === "1";
  const offset = Number(searchParams.get("offset") ?? "0") || 0;

  // Draft query box so typing does not spam the API per keystroke.
  const [draft, setDraft] = useState(q);
  const [items, setItems] = useState<InterestCardType[]>([]);
  const [total, setTotal] = useState(0);
  const [searchSource, setSearchSource] = useState<"keyword">("keyword");
  const [aiAvailable, setAiAvailable] = useState(false);
  const [facets, setFacets] = useState<CategoryCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCategories()
      .then((response) => setFacets(response.items))
      .catch(() => setFacets([]));
  }, []);

  const query = useMemo(
    () => ({
      q,
      category: category ? [category] : undefined,
      mode: mode || undefined,
      beginner: beginner || undefined,
      limit: PAGE_SIZE,
      offset,
    }),
    [q, category, mode, beginner, offset],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listInterests(query);
      setItems(response.items);
      setTotal(response.total);
      setSearchSource(response.search_source);
      setAiAvailable(response.ai_search_available);
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "The catalogue could not be loaded. Check that the API is running.",
      );
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void load();
  }, [load]);

  function updateParams(patch: Record<string, string | null>) {
    const next = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(patch)) {
      if (value === null || value === "") next.delete(key);
      else next.set(key, value);
    }
    setSearchParams(next, { replace: true });
  }

  function submitSearch(event: React.FormEvent) {
    event.preventDefault();
    updateParams({ q: draft.trim(), offset: null });
  }

  const activeFilters = [category, mode, beginner ? "beginner" : ""].filter(Boolean);
  const hasQuery = Boolean(q || activeFilters.length);
  const maxPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);
  const canPrev = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight">Explore the catalogue</h1>
          <p className="mt-2 text-ink-soft">
            Search over {facets.reduce((sum, f) => sum + f.count, 0) || 88} curated
            activities across {facets.length || 10} categories. No account needed
            to browse.
          </p>
        </div>

        {/* Search box */}
        <form onSubmit={submitSearch} className="mt-6 flex max-w-2xl gap-2">
          <label htmlFor="catalogue-search" className="sr-only">
            Search interests
          </label>
          <input
            id="catalogue-search"
            type="search"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Try “paper”, “fermentation”, “balance”, “map”…"
            className="min-h-11 flex-1 rounded-xl border border-line-strong bg-card px-4 text-base placeholder:text-ink-soft/60 focus:border-accent focus:outline-none"
          />
          <button
            type="submit"
            className="min-h-11 rounded-xl bg-accent px-5 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
          >
            Search
          </button>
        </form>

        {/* Filters — only facets the catalogue actually supports (spec 5) */}
        <div className="mt-5 flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => updateParams({ category: null, offset: null })}
              aria-pressed={!category}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
                !category
                  ? "border-accent bg-accent text-white"
                  : "border-line-strong text-ink hover:border-accent hover:text-accent"
              }`}
            >
              All categories
            </button>
            {facets.map((facet) => {
              const active = category === facet.category;
              return (
                <button
                  key={facet.category}
                  onClick={() =>
                    updateParams({
                      category: active ? null : facet.category,
                      offset: null,
                    })
                  }
                  aria-pressed={active}
                  className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
                    active
                      ? "border-accent bg-accent text-white"
                      : "border-line-strong text-ink hover:border-accent hover:text-accent"
                  }`}
                >
                  {facet.category}
                  <span className={`ml-1.5 text-xs ${active ? "text-white/70" : "text-ink-soft"}`}>
                    {facet.count}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-line bg-card p-1">
              {MODE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => updateParams({ mode: option.value || null, offset: null })}
                  aria-pressed={mode === option.value}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    mode === option.value
                      ? "bg-ink text-white"
                      : "text-ink-soft hover:bg-paper-deep hover:text-ink"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <button
              onClick={() =>
                updateParams({ beginner: beginner ? null : "1", offset: null })
              }
              aria-pressed={beginner}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
                beginner
                  ? "border-accent bg-accent text-white"
                  : "border-line-strong text-ink hover:border-accent hover:text-accent"
              }`}
            >
              Beginner-friendly only
            </button>
            {activeFilters.length > 0 && (
              <button
                onClick={() =>
                  setSearchParams(q ? new URLSearchParams({ q }) : new URLSearchParams(), {
                    replace: true,
                  })
                }
                className="px-2 text-sm text-ink-soft underline underline-offset-4 hover:text-clay"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>

        {/* Honest search-source label (spec section 13) */}
        <div className="mt-5 flex flex-wrap items-center justify-between gap-2 text-sm">
          <p aria-live="polite" className="text-ink-soft">
            {loading
              ? "Searching…"
              : `${total} result${total === 1 ? "" : "s"}${q ? ` for “${q}”` : ""}`}
          </p>
          <p className="inline-flex items-center gap-1.5 rounded-full border border-line bg-card px-3 py-1 text-xs text-ink-soft">
            <span
              aria-hidden="true"
              className={`h-1.5 w-1.5 rounded-full ${aiAvailable ? "bg-accent-glow" : "bg-warm"}`}
            />
            {searchSource === "keyword" && !aiAvailable
              ? "Keyword search · AI search not configured"
              : "Keyword search"}
          </p>
        </div>

        {error && (
          <div role="alert" className="mt-4 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
            {error}
          </div>
        )}

        {/* Results */}
        {!loading && !error && items.length === 0 && (
          <div className="mt-8 rounded-2xl border border-dashed border-line-strong bg-card p-10 text-center">
            <p className="text-lg font-semibold">
              {hasQuery ? "Nothing matches that yet." : "The catalogue is empty."}
            </p>
            <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">
              {hasQuery
                ? "Keyword search only reports real matches — it never fabricates suggestions. Try a shorter word, or clear the filters."
                : "Run the seed script (python -m app.seed) to load the sample catalogue."}
            </p>
            {hasQuery && (
              <button
                onClick={() => {
                  setDraft("");
                  setSearchParams(new URLSearchParams(), { replace: true });
                }}
                className="mt-5 rounded-xl border border-line-strong px-5 py-2.5 text-sm font-semibold text-ink hover:border-accent hover:text-accent"
              >
                Reset search
              </button>
            )}
          </div>
        )}

        {loading && (
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-56 animate-pulse rounded-2xl border border-line bg-card" />
            ))}
          </div>
        )}

        {!loading && items.length > 0 && (
          <>
            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((card) => (
                <InterestCard key={card.id} card={card} />
              ))}
            </div>

            {(canPrev || canNext) && (
              <nav
                aria-label="Pagination"
                className="mt-8 flex items-center justify-between gap-4"
              >
                <button
                  disabled={!canPrev}
                  onClick={() => updateParams({ offset: String(Math.max(0, offset - PAGE_SIZE)) })}
                  className="rounded-xl border border-line-strong px-5 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-40"
                >
                  ← Previous
                </button>
                <p className="text-sm text-ink-soft">
                  Page {Math.floor(offset / PAGE_SIZE) + 1} of {maxPage + 1}
                </p>
                <button
                  disabled={!canNext}
                  onClick={() => updateParams({ offset: String(offset + PAGE_SIZE) })}
                  className="rounded-xl border border-line-strong px-5 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next →
                </button>
              </nav>
            )}
          </>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
