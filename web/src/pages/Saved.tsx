import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import InterestCard from "../components/InterestCard";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { ApiRequestError } from "../services/api";
import { listSaved, unsaveInterest } from "../services/catalogue";
import { useSession } from "../hooks/useSession";
import type { InterestCard as InterestCardType } from "../types/api";

export default function Saved() {
  const { session, signIn, loading: authLoading } = useSession();
  const [items, setItems] = useState<InterestCardType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!session) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await listSaved();
      setItems(response.items);
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "Your saved list could not be loaded.",
      );
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleUnsave(slug: string) {
    try {
      const response = await unsaveInterest(slug);
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update your list.");
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Saved interests</h1>
            <p className="mt-2 max-w-2xl text-ink-soft">
              The list is yours: it belongs to your pseudonym, appears to nobody
              else, and disappears when you delete your data.
            </p>
          </div>
          <Link
            to="/explore"
            className="rounded-xl border border-line-strong px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-accent hover:text-accent"
          >
            Browse more →
          </Link>
        </div>

        {/* Signed-out state */}
        {!authLoading && !session && (
          <div className="mt-8 rounded-2xl border border-dashed border-line-strong bg-card p-10 text-center">
            <p className="text-lg font-semibold">Sign in to see your saved list.</p>
            <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">
              Sign-in mints a pseudonym — no email, no password. You can browse the
              full catalogue without one.
            </p>
            <button
              onClick={() => signIn("default")}
              className="mt-5 min-h-11 rounded-xl bg-accent px-6 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
            >
              Sign in with a pseudonym
            </button>
          </div>
        )}

        {session && loading && (
          <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="h-56 animate-pulse rounded-2xl border border-line bg-card" />
            ))}
          </div>
        )}

        {error && (
          <div role="alert" className="mt-6 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
            {error}
          </div>
        )}

        {session && !loading && items.length === 0 && !error && (
          <div className="mt-8 rounded-2xl border border-dashed border-line-strong bg-card p-10 text-center">
            <p className="text-lg font-semibold">Nothing saved yet.</p>
            <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">
              Open any interest and press “Save this interest” — it will wait here
              for you.
            </p>
            <Link
              to="/explore"
              className="mt-5 inline-block min-h-11 rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
            >
              Explore the catalogue
            </Link>
          </div>
        )}

        {session && !loading && items.length > 0 && (
          <>
            <p className="mt-6 text-sm text-ink-soft" aria-live="polite">
              {items.length} saved interest{items.length === 1 ? "" : "s"}
            </p>
            <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((card) => (
                <div key={card.id} className="space-y-2">
                  <InterestCard card={card} />
                  <button
                    onClick={() => handleUnsave(card.slug)}
                    className="w-full text-center text-xs text-ink-soft underline underline-offset-4 hover:text-clay"
                  >
                    Remove from saved
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
