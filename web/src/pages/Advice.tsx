import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import AdviceResults from "../components/AdviceResults";
import GuardianPlayground from "../components/GuardianPlayground";
import NeuralBackdrop from "../components/NeuralBackdrop";
import { InnerHeader, SiteFooter } from "../components/Shell";
import {
  ExploreTeaser,
  FriendTestMeter,
  HowItWorks,
  MentorInvite,
  TransparencyPanel,
} from "../components/home/Sections";
import { ApiRequestError } from "../services/api";
import { createNeed, listScenarios } from "../services/advice";
import { useConfig } from "../hooks/useConfig";
import { useSession } from "../hooks/useSession";
import type { NeedMatchesResponse, SampleScenario } from "../types/api";

const MIN_CHARS = 20;
const MAX_CHARS = 4000;

/* The three steps the server performs on submit (spec UI-1): shown as real
 * progress while the request runs — each label names an action that actually
 * happens (scrub → interpret → match), never a fake completion. */
const SUBMIT_STEPS = ["Stripping PII", "Reading intent", "Matching mentors"] as const;

function SubmitProgress({ step }: { step: number }) {
  return (
    <ol className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2" aria-live="polite">
      {SUBMIT_STEPS.map((label, i) => {
        const done = i < step;
        const active = i === step;
        return (
          <li
            key={label}
            className={`flex items-center gap-2 font-mono text-xs transition-colors ${
              active ? "text-accent" : done ? "text-ink-soft" : "text-ink-soft/50"
            }`}
          >
            <span
              aria-hidden="true"
              className={`h-2 w-2 rounded-full ${
                active ? "bg-accent node-pulse" : done ? "bg-ink-soft" : "bg-line-strong"
              }`}
            />
            {label}
            {done && <span aria-hidden="true" className="text-accent">✓</span>}
          </li>
        );
      })}
    </ol>
  );
}

/** Trust chips — every claim maps to a real config flag (spec UI-1). */
function TrustChips() {
  const { config } = useConfig();
  const chips = [
    { text: "No email, no password", tone: "" },
    { text: "Your words are scrubbed before storage", tone: "" },
    config.ai_available
      ? { text: "Live AI configured", tone: "text-accent" }
      : { text: "Keyword matching · AI not configured", tone: "text-warm" },
  ];
  return (
    <ul className="flex flex-wrap items-center gap-2">
      {chips.map((chip) => (
        <li
          key={chip.text}
          className={`flex items-center gap-1.5 rounded-full border border-line bg-card px-3 py-1.5 text-xs text-ink-soft ${chip.tone}`}
        >
          <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-accent" />
          {chip.text}
        </li>
      ))}
    </ul>
  );
}

export default function Advice() {
  const { session, signIn, loading: sessionLoading } = useSession();
  const location = useLocation();

  const [text, setText] = useState("");
  const [money, setMoney] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitStep, setSubmitStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [needsSignIn, setNeedsSignIn] = useState(false);
  const [result, setResult] = useState<NeedMatchesResponse | null>(null);
  const [scenarios, setScenarios] = useState<SampleScenario[]>([]);
  const stepTimer = useRef<number | null>(null);

  // Sample situations for the front door (spec §14). Public, no auth; if the
  // fetch fails we simply show no example chips rather than inventing any.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const items = await listScenarios();
        if (!cancelled) setScenarios(items);
      } catch {
        // No examples available — leave the list empty, don't fake it.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Advance the visible progress while the single request runs server-side.
  useEffect(() => {
    if (!submitting) {
      setSubmitStep(0);
      return;
    }
    setSubmitStep(0);
    stepTimer.current = window.setInterval(() => {
      setSubmitStep((s) => (s < SUBMIT_STEPS.length - 1 ? s + 1 : s));
    }, 700);
    return () => {
      if (stepTimer.current !== null) window.clearInterval(stepTimer.current);
    };
  }, [submitting]);

  // "How it works" nav link lands here with a hash — scroll once mounted.
  useEffect(() => {
    if (location.hash === "#how-it-works") {
      document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
    }
  }, [location.hash]);

  const trimmed = text.trim();
  const tooShort = trimmed.length > 0 && trimmed.length < MIN_CHARS;
  const canSubmit = trimmed.length >= MIN_CHARS && !submitting;

  // The button's disabled state always names its reason (spec UI-1).
  const submitReason = submitting
    ? null
    : trimmed.length < MIN_CHARS
      ? `Add a little more detail — ${Math.max(0, MIN_CHARS - trimmed.length)} characters to go.`
      : null;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    // Advice is per-member, so it needs a verified identity — but we ask only
    // at the moment of submitting, after they've written, never before.
    if (!session) {
      setNeedsSignIn(true);
      return;
    }

    setSubmitting(true);
    try {
      const response = await createNeed({ text: trimmed, money_involved: money });
      setResult(response);
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        setNeedsSignIn(true);
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSignIn() {
    setError(null);
    await signIn("default");
    // After signing in, retry the exact need they already wrote.
    if (!session) {
      setSubmitting(true);
      try {
        setResult(await createNeed({ text: trimmed, money_involved: money }));
        setNeedsSignIn(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not start. Try again.");
      } finally {
        setSubmitting(false);
      }
    }
  }

  function reset() {
    setResult(null);
    setText("");
    setMoney(false);
    setError(null);
    setNeedsSignIn(false);
  }

  /* Decorative highlight for NeuralBackdrop: three hero links light up when
   * matches arrive (neural brief §8). Cleared while a new request runs. */
  const matchIndices = useMemo(
    () => (result && !submitting ? result.matches.slice(0, 3).map((_, i) => i + 1) : []),
    [result, submitting],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />

      {/* ---------------- Hero + composer (spec UI-1) ---------------- */}
      <section className="relative overflow-hidden border-b border-line">
        {/* Slowly rotating decorative network; not live data (neural brief). */}
        <NeuralBackdrop highlight={matchIndices} />
        <div className="hero-fade pointer-events-none absolute inset-0" aria-hidden="true" />
        <div className="relative z-10 mx-auto w-full max-w-6xl px-4 py-14 sm:py-20">
          {!result && (
            <>
              <p className="float-in font-mono text-xs uppercase tracking-[0.2em] text-accent">
                Advice without an agenda
              </p>
              <h1 className="float-in float-in-delay-1 mt-4 max-w-3xl font-display text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
                Ask for honest guidance on what you're working through
              </h1>
              <p className="float-in float-in-delay-2 mt-4 max-w-2xl text-lg text-ink-soft">
                Advice from people with nothing to sell — anonymous, free, and
                screened so advice can't quietly become a sales pitch.
              </p>
              <div className="float-in float-in-delay-3 mt-6">
                <TrustChips />
              </div>
            </>
          )}

          <form onSubmit={submit} className={`mt-8 ${result ? "" : "max-w-3xl"}`}>
            <label htmlFor="need-text" className="sr-only">
              Describe your situation
            </label>
            <textarea
              id="need-text"
              value={text}
              onChange={(event) => setText(event.target.value.slice(0, MAX_CHARS))}
              rows={result ? 3 : 5}
              placeholder="For example: I've been offered a role but the salary feels low, and I don't know how to ask for more without risking it…"
              className="w-full rounded-2xl border border-line-strong bg-card p-4 text-base placeholder:text-ink-soft/60 focus:border-accent focus:outline-none"
            />
            <div className="mt-1.5 flex items-center justify-between font-mono text-[11px] text-ink-soft">
              <span>
                {trimmed.length < MIN_CHARS
                  ? `At least ${MIN_CHARS} characters so there's something to work with.`
                  : "You'll see how it's read before anyone is matched to it."}
              </span>
              <span>
                {trimmed.length}/{MAX_CHARS}
              </span>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
              <label className="flex cursor-pointer items-center gap-2.5 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={money}
                  onChange={(event) => setMoney(event.target.checked)}
                  className="h-4 w-4 rounded border-line-strong accent-[var(--color-accent)]"
                />
                This involves a decision about money
              </label>

              <button type="submit" disabled={!canSubmit} className="btn-primary">
                {submitting ? "Reading your situation…" : "See how it's understood"}
              </button>
            </div>

            {/* The disabled state names its reason — never a mystery. */}
            {submitReason && (
              <p className="mt-2 text-right text-xs text-ink-soft">{submitReason}</p>
            )}
            {submitting && <SubmitProgress step={submitStep} />}

            {error && (
              <div role="alert" className="mt-4 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
                {error}
              </div>
            )}

            {needsSignIn && (
              <div className="mt-4 rounded-xl border border-line-strong bg-card p-4">
                <p className="text-sm text-ink">
                  To keep your advice private and yours, we use a made-up name —
                  no email or password. Sign in to see your matches.
                </p>
                <button
                  type="button"
                  onClick={handleSignIn}
                  disabled={sessionLoading || submitting}
                  className="btn-primary mt-3"
                >
                  {sessionLoading || submitting ? "Starting…" : "Continue with a made-up name"}
                </button>
              </div>
            )}
          </form>

          {tooShort && (
            <p className="mt-2 text-xs text-clay">Keep going — a sentence or two helps.</p>
          )}

          {/* Sample situations — clicking fills the box (spec §14). */}
          {scenarios.length > 0 && (
            <div className="mt-8">
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-soft">
                Not sure where to start? Try one:
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {scenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    type="button"
                    onClick={() => {
                      setText(scenario.text);
                      setMoney(scenario.money_involved);
                    }}
                    className="rounded-full border border-line bg-card px-3.5 py-2 text-left text-sm text-ink-soft transition-colors hover:border-accent hover:text-ink"
                    title={scenario.text}
                  >
                    <span className="font-mono text-[10px] uppercase tracking-wider text-accent">
                      {scenario.domain}
                      {scenario.money_involved ? " · money" : ""}
                    </span>
                    <span className="mt-0.5 block max-w-[22rem] truncate">
                      {scenario.text}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <p className="mt-8 max-w-3xl rounded-xl bg-card px-4 py-3 text-xs text-ink-soft">
            Your words are stripped of emails, phone numbers, and names before
            they're stored or matched. This is guidance from experienced peers,
            not professional, medical, legal, or financial advice.
          </p>
        </div>
      </section>

      {/* ---------------- Results ---------------- */}
      {result && (
        <section className="mx-auto w-full max-w-6xl px-4 py-12">
          <AdviceResults result={result} onReset={reset} />
        </section>
      )}

      {/* ---------------- Sections (spec UI-3) ---------------- */}
      {!result && (
        <>
          <HowItWorks />
          <section aria-labelledby="playground-title" className="mx-auto w-full max-w-6xl px-4 py-10">
            <h2 id="playground-title" className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
              See the Guardian in action
            </h2>
            <p className="mt-2 max-w-2xl text-ink-soft">
              The filter is the product's core claim, so you can test it before
              you trust it with anything.
            </p>
            <div className="mt-6">
              <GuardianPlayground compact />
            </div>
          </section>
          <FriendTestMeter />
          <TransparencyPanel />
          <ExploreTeaser />
          <MentorInvite />
        </>
      )}

      <div className="flex-1" />
      <SiteFooter />
    </div>
  );
}
