import { useState } from "react";
import { guardianTry } from "../services/advice";
import { ApiRequestError } from "../services/api";
import type { GuardianTryResponse } from "../types/api";

/** Example messages, honestly labelled: two clean, two pitches. */
const EXAMPLES: Array<{ label: string; text: string }> = [
  {
    label: "Clean advice",
    text: "Ask for the salary band in writing before you accept, and compare it with two other offers in your field.",
  },
  {
    label: "Free resource",
    text: "The public library near me runs free résumé workshops every Tuesday — no payment details needed.",
  },
  {
    label: "A pitch",
    text: "My paid course fixes exactly this. Book a call on WhatsApp today — 555 0134 — and I'll give you 20% off if you act now.",
  },
  {
    label: "Soft steering",
    text: "Honestly, everything changed for me once I joined my mentorship group —DM me and I'll send the link.",
  },
];

const ACTION_COPY: Record<string, { title: string; blurb: string; tone: string }> = {
  ALLOW: {
    title: "Allowed",
    blurb: "Nothing promotional detected — the message would pass through untouched.",
    tone: "text-accent",
  },
  WARN: {
    title: "Tagged “possible promotion”",
    blurb: "Flagged for a second look. Severity 2 — a warning tag, not a removal.",
    tone: "text-warm",
  },
  BLOCK_AND_REDACT: {
    title: "Removed and redacted",
    blurb: "Promotion or contact details — the recipient would see a notice instead, and the mentor takes a strike.",
    tone: "text-clay",
  },
};

/**
 * The Guardian playground (spec UI-2): paste a message, see what the Guardian
 * would do to it. Anonymous, rate-limited, and nothing typed is stored or
 * logged — the endpoint scrubs first and never persists. Every result carries
 * its honest source label.
 */
export default function GuardianPlayground({ compact = false }: { compact?: boolean }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<GuardianTryResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimited, setRateLimited] = useState(false);
  const [animateKey, setAnimateKey] = useState(0);

  async function run(value: string) {
    const trimmed = value.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError(null);
    setRateLimited(false);
    try {
      setResult(await guardianTry(trimmed));
      setAnimateKey((k) => k + 1); // restart the redaction animation
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 429) {
        setRateLimited(true);
      } else {
        setError(err instanceof Error ? err.message : "The check failed. Try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  const verdict = result ? ACTION_COPY[result.action] : null;
  const blocked = result?.action === "BLOCK_AND_REDACT";

  return (
    <div className="grad-edge rounded-[20px] bg-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-display text-lg font-semibold">
          Try the Guardian on a message
        </h3>
        <span className="rounded-full border border-line bg-paper px-2.5 py-1 font-mono text-[11px] text-ink-soft">
          anonymous · nothing stored
        </span>
      </div>
      <p className="mt-2 text-sm text-ink-soft">
        Every message in a session runs through this check. Paste or write one
        and see exactly what would happen — this page stores nothing and logs
        nothing you type.
      </p>

      <label htmlFor="guardian-try" className="sr-only">
        Message to check
      </label>
      <textarea
        id="guardian-try"
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, 500))}
        rows={3}
        placeholder="e.g. You should talk to two people in the role before deciding — I can share what I'd ask."
        className="mt-4 w-full rounded-2xl border border-line-strong bg-paper p-3.5 text-sm placeholder:text-ink-soft/60 focus:border-accent focus:outline-none"
      />

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLES.map((example) => (
            <button
              key={example.label}
              type="button"
              onClick={() => {
                setText(example.text);
                void run(example.text);
              }}
              disabled={busy}
              className="rounded-full border border-line px-2.5 py-1 text-[11px] text-ink-soft transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
            >
              {example.label}
            </button>
          ))}
        </div>
        <span className="font-mono text-[11px] text-ink-soft/70">{text.length}/500</span>
      </div>

      <button
        type="button"
        onClick={() => void run(text)}
        disabled={busy || text.trim().length === 0}
        className="btn-primary mt-4"
      >
        {busy ? "Checking…" : "Check this message"}
      </button>
      {text.trim().length === 0 && (
        <p className="mt-1.5 text-xs text-ink-soft">
          Write a message or pick an example above.
        </p>
      )}

      {/* Result — the redaction animation is decorative; the verdict is text. */}
      {result && verdict && (
        <div
          key={animateKey}
          role="status"
          aria-live="polite"
          className={`mt-5 rounded-2xl border border-line bg-paper p-4 ${
            blocked ? "guardian-flash" : ""
          }`}
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className={`font-display text-base font-semibold ${verdict.tone}`}>
              {verdict.title}
            </span>
            <span className="rounded-full bg-card px-2 py-0.5 font-mono text-[11px] text-ink-soft">
              severity {result.severity}
            </span>
            <span className="rounded-full bg-card px-2 py-0.5 font-mono text-[11px] text-ink-soft">
              {result.source === "gemini" ? "AI classifier" : "rules classifier"}
            </span>
          </div>
          <p className="mt-2 text-sm text-ink-soft">{verdict.blurb}</p>

          {/* What the recipient would actually see. */}
          <div className="mt-3 rounded-xl bg-card p-3">
            <p className="font-mono text-[10px] uppercase tracking-wider text-ink-soft/70">
              What the recipient sees
            </p>
            <p
              className={`mt-1.5 whitespace-pre-wrap text-sm ${
                blocked ? "text-ink-soft/60" : "text-ink"
              } ${blocked ? "blur-[2px] select-none" : ""}`}
            >
              {result.display_text}
            </p>
            {blocked && (
              <p className="mt-2 rounded-lg bg-clay-soft px-3 py-2 text-xs text-clay">
                Removed: promotion or contact details.
              </p>
            )}
          </div>

          {result.categories.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {result.categories.map((category) => (
                <span
                  key={category}
                  className="rounded-full bg-card px-2.5 py-1 font-mono text-[11px] text-ink-soft"
                >
                  {category.replace(/_/g, " ").toLowerCase()}
                </span>
              ))}
            </div>
          )}

          <p className="mt-3 font-mono text-[11px] text-ink-soft/70">{result.notice}</p>
        </div>
      )}

      {rateLimited && (
        <p role="alert" className="mt-4 rounded-xl bg-warm-soft px-4 py-3 text-sm text-warm">
          That's the rate limit doing its job — anonymous checks are capped at
          10 per minute. Nothing was stored; try again shortly.
        </p>
      )}
      {error && (
        <p role="alert" className="mt-4 rounded-xl bg-clay-soft px-4 py-3 text-sm text-clay">
          {error}
        </p>
      )}

      {compact && (
        <p className="mt-4 text-xs text-ink-soft">
          The full breakdown — how each category is decided, the strike rule, and
          the evaluation numbers — is on the{" "}
          <a href="/trust" className="text-accent underline underline-offset-4">
            Trust page
          </a>
          .
        </p>
      )}
    </div>
  );
}
