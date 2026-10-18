import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import InterestCard, { CategoryChip } from "../components/InterestCard";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { ApiRequestError } from "../services/api";
import { getInterest, sendFeedback, unsaveInterest } from "../services/catalogue";
import { listSaved, saveInterest } from "../services/catalogue";
import { useSession } from "../hooks/useSession";
import type {
  AgreementSummary,
  FeedbackAction,
  InterestDetail as InterestDetailType,
} from "../types/api";

const RELATIONSHIP_LABELS: Record<string, string> = {
  shares_material: "Shares material",
  shares_technique: "Shares technique",
  shares_skill: "Shares skill",
  shares_way_of_thinking: "Shares a way of thinking",
  related_culture_or_context: "Related culture or context",
  complementary_activity: "Complementary activity",
  prerequisite_for: "Prerequisite for",
  contrasts_with: "Contrasts with",
};

const FEEDBACK_ACTIONS: { action: FeedbackAction; label: string; hint: string }[] = [
  { action: "want_to_try", label: "I want to try this", hint: "Save it as a goal" },
  { action: "already_know", label: "I already know this", hint: "Seen it before" },
  { action: "dismiss", label: "Not for me", hint: "Show less like this" },
];

const REASON_OPTIONS = [
  { value: "not_relevant", label: "Not relevant to me" },
  { value: "too_similar", label: "Too similar to what I've seen" },
  { value: "not_accessible", label: "Not accessible to me" },
];

export default function InterestDetailPage() {
  const { slug = "" } = useParams();
  const { session } = useSession();

  const [detail, setDetail] = useState<InterestDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savedSlugs, setSavedSlugs] = useState<Set<string>>(new Set());
  const [feedbackNote, setFeedbackNote] = useState<string | null>(null);
  const [agreement, setAgreement] = useState<AgreementSummary | null>(null);
  const [reasonFor, setReasonFor] = useState<FeedbackAction | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDetail(await getInterest(slug));
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "That interest could not be loaded.",
      );
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    void load();
  }, [load]);

  // Refresh the saved set whenever the entry changes or auth state changes.
  useEffect(() => {
    if (!session) {
      setSavedSlugs(new Set());
      return;
    }
    listSaved()
      .then((response) => setSavedSlugs(new Set(response.items.map((item) => item.slug))))
      .catch(() => setSavedSlugs(new Set()));
  }, [session, detail?.slug]);

  const isSaved = detail ? savedSlugs.has(detail.slug) : false;

  async function requireAuth(action: () => Promise<void>): Promise<boolean> {
    if (session) {
      await action();
      return true;
    }
    // Save/feedback need an identity; browsing never does.
    setError("Sign in to save interests or give feedback — it takes a pseudonym, not an email.");
    return false;
  }

  async function toggleSave() {
    if (!detail) return;
    await requireAuth(async () => {
      setBusy(true);
      try {
        const response = isSaved
          ? await unsaveInterest(detail.slug)
          : await saveInterest(detail.slug);
        setSavedSlugs(new Set(response.items.map((item) => item.slug)));
        setFeedbackNote(isSaved ? "Removed from your saved list." : "Saved to your list.");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not update your list.");
      } finally {
        setBusy(false);
      }
    });
  }

  async function recordFeedback(action: FeedbackAction) {
    if (!detail) return;
    await requireAuth(async () => {
      setBusy(true);
      try {
        const response = await sendFeedback(detail.slug, action);
        setAgreement(response.agreement);
        setFeedbackNote(
          response.action === "dismiss"
            ? "Noted — this is feedback, not a permanent filter. The entry stays in the catalogue."
            : "Thanks — recorded.",
        );
        setReasonFor(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not record feedback.");
      } finally {
        setBusy(false);
      }
    });
  }

  async function sendReason(action: FeedbackAction, reason: string) {
    if (!detail) return;
    setBusy(true);
    try {
      const response = await sendFeedback(
        detail.slug,
        action,
        reason as "not_relevant" | "too_similar" | "not_accessible",
      );
      setAgreement(response.agreement);
      setFeedbackNote("Thanks — recorded with your reason.");
      setReasonFor(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not record feedback.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Link
          to="/explore"
          className="text-sm text-ink-soft underline-offset-4 hover:text-accent hover:underline"
        >
          ← Back to explore
        </Link>

        {loading && (
          <div className="mt-6 space-y-4" aria-hidden="true">
            <div className="h-8 w-64 animate-pulse rounded bg-line" />
            <div className="h-40 animate-pulse rounded-2xl border border-line bg-card" />
          </div>
        )}

        {error && !detail && (
          <div role="alert" className="mt-6 rounded-2xl border border-clay/30 bg-clay-soft p-8 text-center">
            <p className="font-semibold text-clay">{error}</p>
            <Link
              to="/explore"
              className="mt-4 inline-block rounded-xl border border-clay/40 px-5 py-2.5 text-sm font-semibold text-clay"
            >
              Back to explore
            </Link>
          </div>
        )}

        {detail && (
          <article className="mt-5">
            <div className="flex flex-wrap items-center gap-2">
              <CategoryChip category={detail.category} />
              {detail.difficulty && (
                <span className="rounded-full bg-paper-deep px-2.5 py-1 text-[11px] font-semibold text-ink-soft capitalize">
                  {detail.difficulty}
                </span>
              )}
              {detail.is_sample_content && (
                <span className="rounded-full bg-warm-soft px-2.5 py-1 text-[11px] font-semibold text-warm">
                  Sample entry
                </span>
              )}
            </div>

            <div className="mt-4 grid gap-8 lg:grid-cols-[1.5fr_1fr]">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                  {detail.title}
                </h1>
                <p className="mt-3 text-lg text-ink-soft">{detail.short_description}</p>
                <p className="mt-5 leading-relaxed">{detail.long_description}</p>

                {/* Beginner step */}
                <div className="mt-6 rounded-2xl border-l-4 border-accent/50 bg-accent-soft/60 p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-accent-strong">
                    Your first step
                  </p>
                  <p className="mt-1.5 text-sm leading-relaxed">{detail.beginner_step}</p>
                </div>

                {/* Structured fields (spec section 8) */}
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {detail.skills.length > 0 && (
                    <div className="rounded-xl border border-line bg-card p-4">
                      <h2 className="text-sm font-semibold">Skills practised</h2>
                      <ul className="mt-2 space-y-1 text-sm text-ink-soft">
                        {detail.skills.map((skill) => (
                          <li key={skill}>· {skill}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {detail.materials.length > 0 && (
                    <div className="rounded-xl border border-line bg-card p-4">
                      <h2 className="text-sm font-semibold">Materials</h2>
                      <ul className="mt-2 space-y-1 text-sm text-ink-soft">
                        {detail.materials.map((material) => (
                          <li key={material}>· {material}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {detail.ways_of_thinking.length > 0 && (
                    <div className="rounded-xl border border-line bg-card p-4">
                      <h2 className="text-sm font-semibold">Ways of thinking</h2>
                      <ul className="mt-2 space-y-1 text-sm text-ink-soft">
                        {detail.ways_of_thinking.map((way) => (
                          <li key={way}>· {way}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {detail.accessibility_notes.length > 0 && (
                    <div className="rounded-xl border border-line bg-card p-4">
                      <h2 className="text-sm font-semibold">Access notes</h2>
                      <ul className="mt-2 space-y-1 text-sm text-ink-soft">
                        {detail.accessibility_notes.map((note) => (
                          <li key={note}>· {note}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Source notes */}
                {detail.source_notes && (
                  <p className="mt-5 rounded-xl bg-paper-deep/70 p-4 text-xs text-ink-soft">
                    <span className="font-semibold">Source note: </span>
                    {detail.source_notes}
                  </p>
                )}
              </div>

              {/* Action panel */}
              <aside className="space-y-5">
                <div className="card-raised rounded-2xl border border-line bg-card p-5">
                  <h2 className="text-lg font-semibold">At a glance</h2>
                  <dl className="mt-3 space-y-2.5 text-sm">
                    {detail.time_commitment && (
                      <div className="flex justify-between gap-3">
                        <dt className="text-ink-soft">Time</dt>
                        <dd className="text-right font-medium">{detail.time_commitment}</dd>
                      </div>
                    )}
                    <div className="flex justify-between gap-3">
                      <dt className="text-ink-soft">Formats</dt>
                      <dd className="text-right font-medium capitalize">
                        {[...detail.solo_or_group, ...detail.online_or_in_person]
                          .map((v) => v.replace("_", " "))
                          .join(", ")}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-ink-soft">Languages</dt>
                      <dd className="text-right font-medium uppercase">
                        {detail.languages.join(", ")}
                      </dd>
                    </div>
                  </dl>

                  <button
                    onClick={toggleSave}
                    disabled={busy}
                    aria-pressed={isSaved}
                    className={`mt-5 flex min-h-11 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-60 ${
                      isSaved
                        ? "border border-accent bg-accent-soft text-accent-strong"
                        : "bg-accent text-white hover:bg-accent-strong"
                    }`}
                  >
                    {isSaved ? (
                      <>
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
                          <path d="M9 16.2l-3.5-3.5L4 14.2 9 19.2 20 8.2l-1.4-1.4z" />
                        </svg>
                        Saved
                      </>
                    ) : (
                      <>
                        <svg
                          viewBox="0 0 24 24"
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M6 4h12v16l-6-4-6 4z" strokeLinejoin="round" />
                        </svg>
                        Save this interest
                      </>
                    )}
                  </button>
                  {!session && (
                    <p className="mt-2 text-center text-xs text-ink-soft">
                      Sign-in is required to save — browsing never is.
                    </p>
                  )}
                </div>

                {/* Feedback */}
                <div className="rounded-2xl border border-line bg-card p-5">
                  <h2 className="text-lg font-semibold">How does this land?</h2>
                  <p className="mt-1 text-xs text-ink-soft">
                    One tap records feedback. It never removes the entry for anyone.
                  </p>
                  <div className="mt-3 space-y-2">
                    {FEEDBACK_ACTIONS.map((option) => (
                      <div key={option.action}>
                        <button
                          onClick={() => recordFeedback(option.action)}
                          disabled={busy}
                          className="flex w-full items-center justify-between rounded-xl border border-line px-4 py-2.5 text-left text-sm font-medium transition-colors hover:border-accent hover:text-accent disabled:opacity-60"
                        >
                          {option.label}
                          <span className="text-xs text-ink-soft">{option.hint}</span>
                        </button>
                        {reasonFor === option.action && (
                          <div className="mt-1.5 space-y-1.5 rounded-xl bg-paper p-3">
                            {REASON_OPTIONS.map((reason) => (
                              <button
                                key={reason.value}
                                onClick={() => sendReason(option.action, reason.value)}
                                disabled={busy}
                                className="block w-full rounded-lg border border-line bg-card px-3 py-2 text-left text-xs hover:border-accent"
                              >
                                {reason.label}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={() => setReasonFor(reasonFor ? null : "dismiss")}
                      className="w-full text-left text-xs text-ink-soft underline underline-offset-4 hover:text-accent"
                    >
                      Add an optional reason
                    </button>
                  </div>

                  {agreement && (
                    <div className="mt-4 rounded-xl bg-paper-deep/70 p-3.5 text-xs text-ink-soft">
                      <span className="font-semibold text-ink">
                        {Math.round(agreement.share_matching * 100)}%
                      </span>{" "}
                      of {agreement.sample_size} recorded reactions matched yours.{" "}
                      <span className="italic">({agreement.label})</span>
                    </div>
                  )}
                </div>

                {feedbackNote && (
                  <div
                    role="status"
                    className="rounded-xl border border-accent/30 bg-accent-soft px-4 py-3 text-sm text-accent-strong"
                  >
                    {feedbackNote}
                  </div>
                )}
                {error && detail && (
                  <div
                    role="alert"
                    className="rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay"
                  >
                    {error}{" "}
                    <button onClick={() => setError(null)} className="font-semibold underline">
                      Dismiss
                    </button>
                  </div>
                )}
              </aside>
            </div>

            {/* Related — expanded, labelled relationships */}
            <section aria-labelledby="related-heading" className="mt-12">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id="related-heading" className="text-2xl font-semibold tracking-tight">
                  Connected interests
                </h2>
                <p className="text-sm text-ink-soft">
                  {detail.related.length} explicit relationship
                  {detail.related.length === 1 ? "" : "s"} — each with a stated reason
                </p>
              </div>

              {detail.related.length === 0 ? (
                <p className="mt-4 text-ink-soft">No relationships recorded yet.</p>
              ) : (
                <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {detail.related.map((related) => (
                    <div key={`${related.type}-${related.interest.slug}`} className="space-y-2">
                      <p className="inline-flex items-center gap-1.5 rounded-full bg-ink px-2.5 py-1 text-[11px] font-semibold text-white">
                        {RELATIONSHIP_LABELS[related.type] ?? related.type}
                      </p>
                      {related.note && (
                        <p className="text-xs italic text-ink-soft">“{related.note}”</p>
                      )}
                      <InterestCard card={related.interest} />
                    </div>
                  ))}
                </div>
              )}
            </section>
          </article>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
