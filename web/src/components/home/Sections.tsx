import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPublicStats, listMentors } from "../../services/advice";
import type { PublicStats } from "../../types/api";

const STEPS = [
  {
    title: "Describe your situation",
    body: "Write it in your own words. Your text is stripped of emails, phone numbers, and names before it is stored or matched — no account needed to look around.",
  },
  {
    title: "See how it was read",
    body: "Before anyone is matched, you see the interpretation in plain language and can correct it. You are never matched on a guess you can't check.",
  },
  {
    title: "Talk, protected by the Guardian",
    body: "Every message — both directions — is screened. Promotion, contact solicitation, and urgency tactics are removed automatically. Three strikes and the session ends.",
  },
] as const;

export function HowItWorks() {
  return (
    <section id="how-it-works" aria-labelledby="how-it-works-title" className="mx-auto w-full max-w-6xl px-4 py-16">
      <h2 id="how-it-works-title" className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
        How it works
      </h2>
      <p className="mt-2 max-w-2xl text-ink-soft">
        Three steps, and you can stop after any of them. Nothing is shared with
        a mentor until you start a session.
      </p>
      <ol className="mt-8 grid gap-5 md:grid-cols-3">
        {STEPS.map((step, i) => (
          <li key={step.title} className="grad-edge rounded-[20px] bg-card p-6">
            <span className="font-mono text-xs text-accent">{String(i + 1).padStart(2, "0")}</span>
            <h3 className="mt-2 font-display text-lg font-semibold">{step.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

/** Friend Test meter (spec UI-3): an honest static illustration, labelled. */
export function FriendTestMeter() {
  return (
    <section aria-labelledby="friend-test-title" className="mx-auto w-full max-w-6xl px-4 py-10">
      <div className="grad-edge grid gap-8 rounded-[20px] bg-card p-8 md:grid-cols-2">
        <div>
          <h2 id="friend-test-title" className="font-display text-2xl font-semibold tracking-tight">
            The Friend Test
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            On money decisions, the session tracks one honest question: is this
            mentor pushing you to spend, cautioning you against it, or staying
            neutral? The meter reads their stance across the whole conversation —
            and “pushes to spend” is never softened, whatever came before it.
          </p>
          <p className="mt-3 text-xs text-ink-soft/70">
            Illustration of the three stances — not a live measurement of any session.
          </p>
        </div>
        <div className="flex flex-col justify-center gap-4" aria-hidden="true">
          {[
            { label: "Pushes to spend", active: false, tone: "bg-clay" },
            { label: "Neutral", active: true, tone: "bg-accent" },
            { label: "Cautions against spending", active: false, tone: "bg-warm" },
          ].map((row) => (
            <div key={row.label} className="flex items-center gap-3">
              <span className={`h-3 w-3 rounded-full ${row.active ? row.tone : "bg-line-strong"}`} />
              <div className="h-2 flex-1 rounded-full bg-paper">
                <div
                  className={`h-2 rounded-full ${row.active ? row.tone : "bg-transparent"}`}
                  style={{ width: row.active ? "62%" : "0%" }}
                />
              </div>
              <span
                className={`w-40 text-right text-xs ${row.active ? "font-semibold text-ink" : "text-ink-soft/60"}`}
              >
                {row.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Transparency panel (spec UI-3 + UI-4): the honest public numbers. */
export function TransparencyPanel() {
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [mentors, setMentors] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const value = await getPublicStats();
        if (!cancelled) setStats(value);
      } catch {
        // Endpoint absent or failing — the panel hides rather than invents.
      }
      try {
        const list = await listMentors({ limit: 1 });
        if (!cancelled) setMentors(list.total);
      } catch {
        /* ignore */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const evalRun = stats?.guardian_eval;
  const mentorCount = stats?.mentors.count ?? mentors;

  return (
    <section aria-labelledby="transparency-title" className="mx-auto w-full max-w-6xl px-4 py-10">
      <div className="grad-edge rounded-[20px] bg-card p-8">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="transparency-title" className="font-display text-2xl font-semibold tracking-tight">
            What the Guardian catches — honestly
          </h2>
          <Link to="/trust" className="text-sm font-semibold text-accent underline-offset-4 hover:underline">
            Full trust page →
          </Link>
        </div>

        {mentorCount !== null && (
          <p className="mt-3 text-sm text-ink-soft">
            <span className="font-display text-2xl font-semibold text-ink">{mentorCount}</span>{" "}
            mentors in the directory — every one synthetic, labelled as such on
            their card.
          </p>
        )}

        {evalRun ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-paper p-5">
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                precision
              </p>
              <p className="mt-1 font-display text-3xl font-semibold">
                {Math.round((evalRun.test?.precision ?? 0) * 100)}%
              </p>
              <p className="mt-1 text-xs text-ink-soft">clean advice left alone</p>
            </div>
            <div className="rounded-2xl bg-paper p-5">
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">recall</p>
              <p className="mt-1 font-display text-3xl font-semibold">
                {Math.round((evalRun.test?.recall ?? 0) * 100)}%
              </p>
              <p className="mt-1 text-xs text-ink-soft">pitches caught</p>
            </div>
            <div className="rounded-2xl bg-paper p-5">
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                hard negatives
              </p>
              <p className="mt-1 font-display text-3xl font-semibold">
                {evalRun.test?.hard_negative_fpr === null || evalRun.test?.hard_negative_fpr === undefined
                  ? "—"
                  : `${Math.round(evalRun.test.hard_negative_fpr * 100)}%`}
              </p>
              <p className="mt-1 text-xs text-ink-soft">false alarms on tricky clean advice</p>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-ink-soft">
            No evaluation run available right now — so no numbers are shown. None
            are invented to fill the space.
          </p>
        )}

        {!evalRun?.accuracy_claimed && (
          <p className="mt-5 rounded-xl bg-warm-soft px-4 py-3 text-sm text-warm">
            These numbers describe the current rule behaviour on a fixed 80-message
            gold set whose labels are still machine-generated and unreviewed —
            until people review at least 30 of them, they are not a claim of
            proven accuracy.
          </p>
        )}

        <p className="mt-4 font-mono text-[11px] text-ink-soft/70">
          {stats?.notice ?? "Mentors are synthetic. Evaluation numbers describe rule behaviour, not proven accuracy, until labels are human-reviewed."}
        </p>
      </div>
    </section>
  );
}

export function ExploreTeaser() {
  return (
    <section aria-labelledby="explore-teaser-title" className="mx-auto w-full max-w-6xl px-4 py-10">
      <div className="grad-edge flex flex-col items-start gap-5 rounded-[20px] bg-card p-8 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 id="explore-teaser-title" className="font-display text-xl font-semibold tracking-tight">
            Small things to try yourself
          </h2>
          <p className="mt-2 max-w-xl text-sm text-ink-soft">
            A catalogue of activities and crafts with honest, written reasons
            why two things are related. Browse it without an account — it is
            sample content, labelled as such on every entry.
          </p>
        </div>
        <Link to="/explore" className="btn-ghost shrink-0">
          Open Explore
        </Link>
      </div>
    </section>
  );
}

export function MentorInvite() {
  return (
    <section aria-labelledby="mentor-invite-title" className="mx-auto w-full max-w-6xl px-4 py-10">
      <div className="grad-edge rounded-[20px] bg-card p-8 text-center">
        <h2 id="mentor-invite-title" className="font-display text-xl font-semibold tracking-tight">
          Would you mentor here?
        </h2>
        <p className="mx-auto mt-2 max-w-xl text-sm text-ink-soft">
          Mentors in this prototype are synthetic, and there is no sign-up yet —
          the honest state of things. The design goal is a place where your
          advice can't quietly turn into a sales funnel: the Guardian screens
          every message in both directions, and promotion ends your session.
        </p>
        <p className="mt-4 font-mono text-[11px] uppercase tracking-wider text-ink-soft/70">
          Real mentor accounts are not built yet — nothing is collected for them.
        </p>
      </div>
    </section>
  );
}
