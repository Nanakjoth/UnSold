import { useEffect, useState } from "react";
import GuardianPlayground from "../components/GuardianPlayground";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { getPublicStats } from "../services/advice";
import type { PublicStats } from "../types/api";

/** What the Guardian looks for, and what happens — the full rule table. */
const CATEGORIES = [
  {
    name: "Direct promotion",
    example: "“My paid course fixes exactly this.”",
    action: "Removed (severity 3) · strike",
  },
  {
    name: "Contact solicitation",
    example: "“WhatsApp me on 555 0134 and we'll talk offline.”",
    action: "Removed (severity 3) · strike",
  },
  {
    name: "Urgency / fear",
    example: "“Book today or lose the slot forever.”",
    action: "Removed (severity 3) · strike",
  },
  {
    name: "Soft steering",
    example: "“DM me and I'll send the link.”",
    action: "Tagged “possible promotion” (severity 2)",
  },
  {
    name: "Affiliate / referral",
    example: "“Use my link and we both get a discount.”",
    action: "Removed (severity 3) · strike",
  },
] as const;

const KNOWN_LIMITS = [
  "The rules classifier covers English and Spanish phrase sets plus contact patterns that are language-agnostic. A live AI classifier would widen this; until one is configured, other languages are less well covered — and we say so rather than hiding it.",
  "Mentors here are synthetic. Their replies come from a simulator with three voices (honest, salesy, subtle) so the Guardian can be exercised — never a real person.",
  "The evaluation numbers below come from a fixed 80-message gold set whose labels are machine-generated and still unreviewed. Until people review at least 30 of them, the numbers describe current rule behaviour, not proven accuracy.",
  "The mentor's half of the identity-reveal consent is simulated, because mentors don't authenticate in this prototype.",
] as const;

export default function Trust() {
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const value = await getPublicStats();
        if (!cancelled) setStats(value);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const evalRun = stats?.guardian_eval;

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-12">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent">Trust</p>
        <h1 className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
          How the Guardian decides — and how it's checked
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-ink-soft">
          The filter is the product's core claim. Here is the whole mechanism:
          what it looks for, what it does, how it's evaluated, and where it is
          honestly not good enough yet.
        </p>

        {/* 1 — Try it yourself. */}
        <section aria-labelledby="trust-try" className="mt-12">
          <h2 id="trust-try" className="font-display text-2xl font-semibold tracking-tight">
            1 · Try it yourself
          </h2>
          <div className="mt-5">
            <GuardianPlayground />
          </div>
        </section>

        {/* 2 — How a message is decided. */}
        <section aria-labelledby="trust-rules" className="mt-14">
          <h2 id="trust-rules" className="font-display text-2xl font-semibold tracking-tight">
            2 · What it looks for
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-ink-soft">
            Rules first (deterministic, auditable), an AI classifier layered on
            when one is configured, and — most importantly — the{" "}
            <span className="font-semibold text-ink">action is decided by code,
            never by the model</span>. Three strikes end the session.
          </p>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[36rem] text-sm">
              <thead>
                <tr className="border-b border-line text-left font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                  <th className="py-2 pr-4 font-normal">Category</th>
                  <th className="py-2 pr-4 font-normal">Example it catches</th>
                  <th className="py-2 font-normal">Action</th>
                </tr>
              </thead>
              <tbody>
                {CATEGORIES.map((row) => (
                  <tr key={row.name} className="border-b border-line/60">
                    <td className="py-3 pr-4 font-medium">{row.name}</td>
                    <td className="py-3 pr-4 text-ink-soft">{row.example}</td>
                    <td className="py-3 text-ink-soft">{row.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 max-w-2xl text-sm text-ink-soft">
            Clean advice that merely <span className="italic">mentions</span> a
            course, certification, or paid option is a hard negative — it must
            pass, and the evaluation tracks exactly that failure mode.
          </p>
        </section>

        {/* 3 — The numbers, honestly framed. */}
        <section aria-labelledby="trust-numbers" className="mt-14">
          <h2 id="trust-numbers" className="font-display text-2xl font-semibold tracking-tight">
            3 · How it's checked
          </h2>

          {failed && (
            <p className="mt-4 rounded-xl bg-warm-soft px-4 py-3 text-sm text-warm">
              The stats endpoint is unavailable right now — so no numbers are
              shown. None are invented to fill the space.
            </p>
          )}

          {!failed && !evalRun && (
            <p className="mt-4 rounded-xl bg-warm-soft px-4 py-3 text-sm text-warm">
              No evaluation run available — so no numbers are shown.
            </p>
          )}

          {evalRun && (
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <div className="grad-edge rounded-[20px] bg-card p-6">
                <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                  precision
                </p>
                <p className="mt-1 font-display text-4xl font-semibold">
                  {Math.round((evalRun.test?.precision ?? 0) * 100)}%
                </p>
                <p className="mt-1 text-xs text-ink-soft">
                  clean advice left untouched
                </p>
              </div>
              <div className="grad-edge rounded-[20px] bg-card p-6">
                <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                  recall
                </p>
                <p className="mt-1 font-display text-4xl font-semibold">
                  {Math.round((evalRun.test?.recall ?? 0) * 100)}%
                </p>
                <p className="mt-1 text-xs text-ink-soft">pitches caught</p>
              </div>
              <div className="grad-edge rounded-[20px] bg-card p-6">
                <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                  false alarms
                </p>
                <p className="mt-1 font-display text-4xl font-semibold">
                  {evalRun.test?.hard_negative_fpr === null ||
                  evalRun.test?.hard_negative_fpr === undefined
                    ? "—"
                    : `${Math.round(evalRun.test.hard_negative_fpr * 100)}%`}
                </p>
                <p className="mt-1 text-xs text-ink-soft">
                  on hard-negative clean advice
                </p>
              </div>
            </div>
          )}

          <div className="mt-5 rounded-2xl bg-warm-soft px-5 py-4">
            <p className="text-sm font-semibold text-warm">
              {evalRun?.accuracy_claimed
                ? "Labels human-reviewed."
                : "These are not a claim of proven accuracy."}
            </p>
            <p className="mt-1.5 text-sm text-warm/90">
              {evalRun
                ? `${evalRun.labels_reviewed} of ${evalRun.total_labels} gold-set labels reviewed so far — people must review at least 30 before these numbers count as accuracy rather than a description of current behaviour.${evalRun.run_at ? ` Last run: ${new Date(evalRun.run_at).toLocaleString()}.` : ""}`
                : "The gold-set labels are machine-generated and unreviewed."}
            </p>
          </div>

          <p className="mt-4 max-w-2xl text-sm text-ink-soft">
            {stats?.notice ??
              "All mentors are synthetic. Evaluation numbers describe rule behaviour, not proven accuracy, until labels are human-reviewed."}
          </p>
        </section>

        {/* 4 — Privacy in the session. */}
        <section aria-labelledby="trust-privacy" className="mt-14">
          <h2 id="trust-privacy" className="font-display text-2xl font-semibold tracking-tight">
            4 · What happens to your words
          </h2>
          <ul className="mt-4 max-w-3xl space-y-3 text-sm text-ink-soft">
            <li className="flex gap-3">
              <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              Emails, phone numbers, URLs, handles, and names are scrubbed{" "}
              <span className="font-semibold text-ink">before storage and before
              any model call</span> — raw text never reaches the database or a prompt.
            </li>
            <li className="flex gap-3">
              <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              Blocked messages are stored only in scrubbed, redacted form for
              audit; the other side sees a notice, not the text.
            </li>
            <li className="flex gap-3">
              <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              The playground above stores and logs{" "}
              <span className="font-semibold text-ink">nothing</span> you type —
              it runs the same scrub + screen pipeline without any persistence.
            </li>
            <li className="flex gap-3">
              <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              Deleting your account removes your needs, sessions, messages, and
              feedback — the deletion cascades and returns exact counts.
            </li>
          </ul>
        </section>

        {/* 5 — Known limits, plainly. */}
        <section aria-labelledby="trust-limits" className="mt-14">
          <h2 id="trust-limits" className="font-display text-2xl font-semibold tracking-tight">
            5 · Where it's honestly not good enough
          </h2>
          <ul className="mt-4 max-w-3xl space-y-3 text-sm text-ink-soft">
            {KNOWN_LIMITS.map((limit) => (
              <li key={limit} className="flex gap-3">
                <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-warm" />
                {limit}
              </li>
            ))}
          </ul>
        </section>

        <div className="mt-14 flex flex-wrap gap-3">
          <a href="/metrics" className="btn-ghost">
            Full metrics page
          </a>
          <a href="/privacy" className="btn-ghost">
            Privacy details
          </a>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
