import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ProvenanceChip from "./ProvenanceChip";
import type { MentorMatch, NeedMatchesResponse } from "../types/api";
import { createSession } from "../services/sessions";

const DISTRESS_COPY: Record<string, string> = {
  none: "",
  mild: "",
  moderate:
    "What you're describing sounds heavy. If it ever feels like more than a decision, please also reach out to someone you trust or a local support line — a mentor is a peer, not a professional.",
  high:
    "I'm sorry you're carrying this. A mentor can talk it through with you, but this sounds like it also deserves support from someone trained — please consider contacting a local support line or someone you trust now.",
};

function MatchCard({ match, needId }: { match: MentorMatch; needId: string }) {
  const navigate = useNavigate();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const card = match.mentor.public_card;

  async function startSession() {
    setStarting(true);
    setError(null);
    try {
      const session = await createSession({ mentor_id: match.mentor.id, need_id: needId });
      navigate(`/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start a session.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <article className="grad-edge float-in rounded-[20px] bg-card p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
            {card.role_band}
          </p>
          <h3 className="mt-1 font-display text-xl font-semibold tracking-tight">
            {match.mentor.pseudonym}
          </h3>
        </div>
        {/* Fit score + type as badges (spec UI-4). */}
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <span className="rounded-full bg-accent-soft px-2.5 py-1 font-mono text-[11px] font-semibold text-accent">
            fit {(match.fit_score * 100).toFixed(0)}
          </span>
          <span
            className={`rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider ${
              match.match_type === "DIRECT"
                ? "bg-card text-accent"
                : "bg-paper text-ink-soft"
            }`}
          >
            {match.match_type === "DIRECT" ? "direct fit" : "cross-domain"}
          </span>
        </div>
      </div>

      {/* The reason they fit — grounded in the card and your intent only. */}
      <p className="mt-4 text-sm leading-relaxed text-ink-soft">{match.explanation}</p>

      {match.cross_domain_value && (
        <p className="mt-2 text-sm text-ink-soft">
          <span className="font-medium text-ink">Why it may help: </span>
          {match.cross_domain_value}
        </p>
      )}

      {match.watch_outs.length > 0 && (
        <div className="mt-4 rounded-2xl bg-paper p-4">
          <p className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
            Worth knowing
          </p>
          <ul className="mt-2 space-y-1.5">
            {match.watch_outs.map((w) => (
              <li key={w.note} className="flex gap-2 text-xs text-ink-soft">
                <span aria-hidden="true" className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-warm" />
                {w.note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {match.starter_questions.length > 0 && (
        <div className="mt-4">
          <p className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
            To get started, you could ask
          </p>
          <ul className="mt-2 space-y-2">
            {match.starter_questions.map((q) => (
              <li key={q} className="flex gap-2.5 text-sm text-ink-soft">
                <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" />
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-line pt-3.5">
        {card.languages.map((lang) => (
          <span
            key={lang}
            className="rounded-full bg-paper px-2.5 py-1 font-mono text-[10px] text-ink-soft"
          >
            {lang}
          </span>
        ))}
        <span className="font-mono text-[10px] text-ink-soft">
          {card.seniority_band} · {card.country_code}
        </span>
        {match.mentor.is_synthetic && (
          <span className="ml-auto rounded-full border border-warm/40 bg-warm-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-warm">
            Synthetic mentor
          </span>
        )}
      </div>

      {/* The core CTA: open a Guardian-protected session with this mentor. */}
      <div className="mt-4">
        <button onClick={startSession} disabled={starting} className="btn-primary w-full">
          {starting ? "Opening a session…" : "Start a session"}
        </button>
        <p className="mt-2 text-center text-[11px] text-ink-soft/80">
          Every message is screened by the Guardian — mentors can't sell or share
          contact details.
        </p>
        {error && <p className="mt-2 text-center text-xs text-clay">{error}</p>}
      </div>
    </article>
  );
}

export default function AdviceResults({
  result,
  onReset,
}: {
  result: NeedMatchesResponse;
  onReset: () => void;
}) {
  const { interpretation, matches, no_strong_match, retrieval_source, notice } = result;
  const intent = interpretation.intent;
  const distress = DISTRESS_COPY[intent.distress_level] ?? "";

  return (
    <div>
      {/* How we read your situation — shown so it can be checked (spec §2.1). */}
      <section aria-labelledby="interp" className="grad-edge rounded-[20px] bg-card p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="interp" className="font-display text-xl font-semibold tracking-tight">
            How we read your situation
          </h2>
          <ProvenanceChip source={interpretation.interpretation_source} context="interpretation" />
        </div>
        <p className="mt-4 text-ink">“{interpretation.summary}”</p>

        <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-3 text-sm">
          <div>
            <dt className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">Goal</dt>
            <dd className="mt-0.5 font-medium">{intent.goal_type.replace(/_/g, " ")}</dd>
          </div>
          {intent.domains.length > 0 && (
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">Areas</dt>
              <dd className="mt-0.5 font-medium">{intent.domains.join(", ")}</dd>
            </div>
          )}
          <div>
            <dt className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
              Money involved
            </dt>
            <dd className="mt-0.5 font-medium">{intent.money_involved ? "Yes" : "No"}</dd>
          </div>
        </dl>

        {intent.risk_flags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {intent.risk_flags.map((flag) => (
              <span
                key={flag}
                className="rounded-full bg-clay-soft px-2.5 py-1 font-mono text-[11px] text-clay"
              >
                {flag.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}

        {interpretation.clarifying_questions.length > 0 && (
          <div className="mt-5 rounded-2xl bg-paper p-4">
            <p className="text-sm font-semibold">A couple of things that would sharpen this</p>
            <ul className="mt-2.5 space-y-2.5">
              {interpretation.clarifying_questions.map((cq) => (
                <li key={cq.question}>
                  <p className="text-sm text-ink">{cq.question}</p>
                  <p className="mt-0.5 text-xs text-ink-soft">{cq.why}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {distress && (
          <p className="mt-5 rounded-2xl border-l-4 border-accent/40 bg-paper py-3.5 pr-4 pl-4 text-sm text-ink-soft">
            {distress}
          </p>
        )}
      </section>

      {/* Matches */}
      <section aria-labelledby="matches" className="mt-10">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="matches" className="font-display text-2xl font-semibold tracking-tight">
            {no_strong_match ? "Closest mentors we have" : "People who can help"}
          </h2>
          <ProvenanceChip source={retrieval_source} context="ranking" />
        </div>

        {notice && (
          <p className="mt-4 rounded-2xl border border-dashed border-line-strong bg-card px-4 py-3 text-sm text-ink-soft">
            {notice}
          </p>
        )}

        {matches.length === 0 ? (
          <p className="mt-4 text-ink-soft">
            No mentor matched. Try adding a detail or two about what you're facing.
          </p>
        ) : (
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            {matches.map((match) => (
              <MatchCard key={match.mentor.id} match={match} needId={result.need_id} />
            ))}
          </div>
        )}
      </section>

      <div className="mt-10 flex flex-wrap gap-3">
        <button onClick={onReset} className="btn-ghost">
          Describe something else
        </button>
        <a href="/explore" className="btn-ghost">
          Or explore activities to try yourself →
        </a>
      </div>
    </div>
  );
}
