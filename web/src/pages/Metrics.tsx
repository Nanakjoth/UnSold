import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { getEvalRun, getGuardianMetrics } from "../services/sessions";
import type { AgreementMetric, EvalRun } from "../types/api";

/**
 * The Guardian metrics view: offline evaluation (spec §12) + online agreement
 * (CORE_REALIGNMENT P2.4).
 *
 * Honesty rules baked in: the offline numbers carry their sample size + split
 * and are NOT accuracy while labels are unreviewed; the online share is hidden
 * below 3 samples and labelled simulated while mentors are synthetic.
 */

export default function Metrics() {
  const [metric, setMetric] = useState<AgreementMetric | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [evalRun, setEvalRun] = useState<EvalRun | null>(null);
  const [evalNotice, setEvalNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const body = await getGuardianMetrics();
        if (!cancelled) {
          setMetric(body.agreement);
          setNotice(body.notice ?? null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load metrics.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Stage P3: the last offline evaluation run (spec §12). Optional — a 404 just
  // means no run exists yet, which is an honest state, not an error.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const body = await getEvalRun();
        if (!cancelled) {
          setEvalRun(body.run);
          setEvalNotice(body.notice ?? null);
        }
      } catch {
        // No eval run yet — leave the section hidden.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-12">
        <h1 className="text-3xl font-semibold tracking-tight">Does the Guardian get it right?</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          The Guardian removes promotion and contact details automatically. This view checks
          whether its calls match what mentees actually felt — because a filter nobody agrees
          with is just noise.
        </p>

        {loading && (
          <div className="mt-8 rounded-2xl border border-line bg-card p-8 text-sm text-ink-soft">
            Loading metrics…
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="mt-8 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay"
          >
            {error}
          </div>
        )}

        {!loading && !error && metric && (
          <>
            {/* The headline number — always with its sample size, never alone. */}
            <section className="mt-8 rounded-2xl border border-line bg-card p-7">
              <div className="flex flex-wrap items-baseline gap-3">
                <p className="text-5xl font-semibold tracking-tight text-accent">
                  {metric.share === null ? "—" : `${Math.round(metric.share * 100)}%`}
                </p>
                <p className="text-sm text-ink-soft">
                  agreement across {metric.sample_size} session
                  {metric.sample_size === 1 ? "" : "s"}
                </p>
              </div>

              <p className="mt-4 text-sm leading-relaxed text-ink-soft">{metric.label}</p>

              {/* Sub-counts behind the number — it is never unexplained. */}
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-paper p-4">
                  <p className="text-2xl font-semibold">{metric.guardian_flagged}</p>
                  <p className="mt-1 text-xs text-ink-soft">
                    sessions where the Guardian flagged a pitch (severity 2+)
                  </p>
                </div>
                <div className="rounded-xl bg-paper p-4">
                  <p className="text-2xl font-semibold">{metric.mentee_reported_pitch}</p>
                  <p className="mt-1 text-xs text-ink-soft">
                    sessions where the mentee said it felt like a pitch
                  </p>
                </div>
              </div>

              {metric.share === null && (
                <p className="mt-5 rounded-xl bg-warm/20 px-4 py-3 text-sm text-ink-soft">
                  We need at least 3 honest responses before reporting a share — a percentage
                  built from a couple of sessions would mislead more than it informs.
                </p>
              )}

              {metric.is_simulated && (
                <p className="mt-4 text-[11px] uppercase tracking-wide text-ink-soft/70">
                  Simulated — all mentors in this prototype are synthetic
                </p>
              )}
            </section>

            {notice && (
              <p className="mt-4 text-xs leading-relaxed text-ink-soft/80">{notice}</p>
            )}

            {/* How the metric works — legible, not a black box. */}
            <section className="mt-6 rounded-2xl border border-line bg-paper p-7">
              <h2 className="text-lg font-semibold">How this is calculated</h2>
              <ul className="mt-3 space-y-2 text-sm text-ink-soft">
                <li>
                  We compare two independent calls per session: the Guardian's verdict (did any
                  message reach severity 2?) and the mentee's own report (&ldquo;did it feel like
                  a pitch?&rdquo;).
                </li>
                <li>
                  Sessions where the mentee answered &ldquo;unsure&rdquo; are excluded rather
                  than guessed for.
                </li>
                <li>
                  A disagreement is logged for human review — it never triggers an automatic
                  action against anyone.
                </li>
              </ul>
              <Link
                to="/sessions"
                className="mt-5 inline-block text-sm font-semibold text-accent underline-offset-4 hover:underline"
              >
                Give feedback on a finished session →
              </Link>
            </section>

            {/* Stage P3: offline evaluation (spec §12) — the fixed gold set. */}
            {evalRun && (
              <section className="mt-6 rounded-2xl border border-line bg-card p-7">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold">Offline evaluation (gold set)</h2>
                  <span className="rounded-full bg-paper-deep px-2.5 py-1 text-[11px] text-ink-soft">
                    split: {evalRun.split} · n={evalRun.n}
                  </span>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl bg-paper p-4">
                    <p className="text-2xl font-semibold">{(evalRun.precision * 100).toFixed(0)}%</p>
                    <p className="mt-1 text-xs text-ink-soft">precision</p>
                  </div>
                  <div className="rounded-xl bg-paper p-4">
                    <p className="text-2xl font-semibold">{(evalRun.recall * 100).toFixed(0)}%</p>
                    <p className="mt-1 text-xs text-ink-soft">recall</p>
                  </div>
                  <div className="rounded-xl bg-paper p-4">
                    <p className="text-2xl font-semibold">{(evalRun.f1 * 100).toFixed(0)}%</p>
                    <p className="mt-1 text-xs text-ink-soft">F1</p>
                  </div>
                </div>

                <p className="mt-4 text-sm text-ink-soft">
                  Hard-negative false-positive rate:{" "}
                  <span className="font-semibold text-ink">
                    {evalRun.hard_negative_fpr === null
                      ? "—"
                      : `${(evalRun.hard_negative_fpr * 100).toFixed(0)}%`}
                  </span>{" "}
                  across {evalRun.hard_negative_count} hard negatives (clean advice that mentions
                  courses or certifications but must never be blocked).
                </p>

                {/* Per-category recall — where it is strong, where it still misses. */}
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                    Recall by category
                  </h3>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    {Object.entries(evalRun.per_category_recall).map(([cat, r]) => (
                      <div
                        key={cat}
                        className="flex items-center justify-between rounded-lg bg-paper px-3 py-2 text-sm"
                      >
                        <span className="text-ink-soft">{cat.replace(/_/g, " ").toLowerCase()}</span>
                        <span className="font-medium">
                          {(r * 100).toFixed(0)}%
                          <span className="ml-1 text-[11px] text-ink-soft/70">
                            ({evalRun.per_category_support[cat]})
                          </span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* The confusion matrix — never a bare accuracy number. */}
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                    Confusion matrix
                  </h3>
                  <div className="mt-2 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs text-ink-soft">
                          <th className="py-1 pr-4 font-normal">actual ↓ / predicted →</th>
                          <th className="py-1 pr-4 font-normal">clean</th>
                          <th className="py-1 font-normal">pitch</th>
                        </tr>
                      </thead>
                      <tbody>
                        {["actual_clean", "actual_pitch"].map((actual) => (
                          <tr key={actual} className="border-t border-line">
                            <td className="py-1.5 pr-4 text-ink-soft">
                              {actual === "actual_clean" ? "clean" : "pitch"}
                            </td>
                            <td className="py-1.5 pr-4">
                              {evalRun.confusion[actual]?.predicted_clean ?? 0}
                            </td>
                            <td className="py-1.5">{evalRun.confusion[actual]?.predicted_pitch ?? 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Honesty: unreviewed labels are NOT accuracy. */}
                {evalRun.review_status !== "reviewed" ? (
                  <p className="mt-5 rounded-xl bg-warm/20 px-4 py-3 text-sm text-ink-soft">
                    These labels are still marked &ldquo;unreviewed&rdquo; — until people review
                    at least 30 of them, these numbers describe the current behaviour, not
                    proven accuracy.
                  </p>
                ) : (
                  <p className="mt-5 rounded-xl bg-accent-soft px-4 py-3 text-sm text-accent-strong">
                    Labels human-reviewed.
                  </p>
                )}

                {evalNotice && (
                  <p className="mt-3 text-xs leading-relaxed text-ink-soft/80">{evalNotice}</p>
                )}
              </section>
            )}
          </>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
