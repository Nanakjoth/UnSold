import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { useSession } from "../hooks/useSession";
import { listMentors } from "../services/advice";
import {
  createSession,
  editSummary,
  endSession,
  getFriendTest,
  getSession,
  getSummary,
  listMessages,
  listSessions,
  requestMentorReply,
  sendMessage,
  setReveal,
  submitFeedback,
} from "../services/sessions";
import type {
  FeltPitched,
  FriendTestResult,
  GuardianDecision,
  RevealResponse,
  Session as SessionType,
  SessionMessage,
  SessionSummary,
} from "../types/api";

/** Honest label: every mentor in this prototype is synthetic, and replies come
 * from the simulator (spec §10.12) — never a live human. */
const SIM_BANNER =
  "This mentor is synthetic. Replies come from a simulator, not a real person.";

const ACTION_COPY: Record<string, string> = {
  ALLOW: "",
  WARN: "Possible promotion",
  BLOCK_AND_REDACT: "Removed: promotion or contact details",
};

/** Small status icon per Guardian state (spec UI-4: bubble states). */
function GuardianGlyph({ action }: { action: string }) {
  if (action === "BLOCK_AND_REDACT") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-clay" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <circle cx="8" cy="8" r="6.2" />
        <path d="M4.5 11.5l7-7" />
      </svg>
    );
  }
  if (action === "WARN") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-warm" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 2.2l6 11H2z" />
        <path d="M8 6.6v3M8 11.6v.1" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-accent" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 8.6l3 3 7-7.2" />
    </svg>
  );
}

function ActionTag({ action }: { action: string }) {
  const label = ACTION_COPY[action];
  if (!label) return null;
  const blocked = action === "BLOCK_AND_REDACT";
  return (
    <span
      className={`mt-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${
        blocked ? "bg-clay-soft text-clay" : "bg-warm-soft text-warm"
      }`}
    >
      <GuardianGlyph action={action} />
      {label}
    </span>
  );
}

function Bubble({ message }: { message: SessionMessage }) {
  const mine = message.sender_role === "mentee";
  const blocked = message.action === "BLOCK_AND_REDACT";
  const warned = message.action === "WARN";
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 transition-shadow ${
          mine
            ? blocked
              ? "border border-clay/40 bg-clay-soft text-clay"
              : warned
                ? "border border-warm/40 bg-warm-soft text-warm"
                : "bg-accent text-white"
            : "border border-line bg-card text-ink"
        }`}
      >
        {/* The recipient-facing text — differs from stored when redacted. */}
        <p className={`whitespace-pre-wrap text-sm ${blocked ? "blur-[2px] select-none" : ""}`}>
          {message.display_text}
        </p>
        {!mine && message.is_simulated && (
          <p className="mt-1.5 font-mono text-[10px] uppercase tracking-wider text-ink-soft/70">
            Simulated mentor
          </p>
        )}
        <ActionTag action={message.action} />
      </div>
    </div>
  );
}

function FriendTestPanel({ result }: { result: FriendTestResult }) {
  if (!result.applicable) {
    return (
      <div className="rounded-2xl bg-paper px-4 py-3 text-xs text-ink-soft">
        {result.label}
      </div>
    );
  }
  const alert = result.stance === "pushes_to_spend";
  return (
    <div
      className={`rounded-2xl px-4 py-3 text-sm ${
        alert ? "border border-clay/40 bg-clay-soft text-clay" : "bg-paper text-ink-soft"
      }`}
    >
      <p className="font-mono text-[10px] uppercase tracking-wider">Friend Test</p>
      <p className="mt-1">{result.label}</p>
      {result.is_simulated && (
        <p className="mt-1 text-[11px] opacity-70">Simulated — this mentor is not a real person.</p>
      )}
    </div>
  );
}

// --- Stage A3: reveal consent (spec section 8) ------------------------------

function RevealPanel({
  sessionId,
  reveal,
  onDone,
}: {
  sessionId: string;
  reveal: SessionType["reveal"];
  onDone: (r: RevealResponse) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [contact, setContact] = useState("");
  const [error, setError] = useState<string | null>(null);
  const revealed = reveal.mentee_consent && reveal.mentor_consent;

  async function decide(consent: boolean) {
    setBusy(true);
    setError(null);
    try {
      onDone(await setReveal(sessionId, consent, consent ? contact || undefined : undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update consent.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grad-edge rounded-[20px] bg-card p-5">
      <h3 className="font-display text-base font-semibold">Stay anonymous, or reveal to each other</h3>
      <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">
        You both keep your made-up names unless you both agree to reveal. If you reveal, you'll
        only see each other's display name and whatever contact you choose to share — never a
        real identity. You can change your mind until both sides have said yes.
      </p>
      {revealed ? (
        <div className="mt-3 space-y-1.5">
          <p className="rounded-xl bg-accent-soft px-3 py-2 text-xs text-accent">
            Revealed. Only display names and chosen contacts are shared.
          </p>
          <p className="font-mono text-[11px] text-ink-soft/70">
            {reveal.revealed_at && `Shared ${new Date(reveal.revealed_at).toLocaleString()}`}
          </p>
        </div>
      ) : (
        <>
          {!reveal.mentee_consent && (
            <div className="mt-3 flex flex-wrap items-end gap-2">
              <label className="flex-1">
                <span className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
                  Contact to share (optional)
                </span>
                <input
                  value={contact}
                  onChange={(e) => setContact(e.target.value.slice(0, 200))}
                  placeholder="e.g. a handle or email you're happy to share"
                  className="mt-1 w-full rounded-xl border border-line-strong bg-paper px-3 py-2 text-sm placeholder:text-ink-soft/50 focus:border-accent focus:outline-none"
                />
              </label>
              <button
                onClick={() => void decide(true)}
                disabled={busy}
                className="btn-primary rounded-xl px-4 py-2 text-sm"
              >
                Reveal
              </button>
            </div>
          )}
          {reveal.mentee_consent && !revealed && (
            <button
              onClick={() => void decide(false)}
              disabled={busy}
              className="btn-ghost mt-3 rounded-xl px-4 py-2 text-sm disabled:opacity-50"
            >
              Withdraw consent
            </button>
          )}
        </>
      )}
      {error && (
        <p role="alert" className="mt-2 text-xs text-clay">
          {error}
        </p>
      )}
    </div>
  );
}

// --- Stage A3: editable summary (spec section 10.8) -------------------------

function SummaryPanel({ sessionId }: { sessionId: string }) {
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<{ key_points: string; action_items: string; caveats: string }>(
    { key_points: "", action_items: "", caveats: "" },
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const s = await getSummary(sessionId);
        if (!cancelled) {
          setSummary(s);
          setDraft({
            key_points: s.key_points.join("\n"),
            action_items: s.action_items.join("\n"),
            caveats: s.caveats.join("\n"),
          });
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load the summary.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const split = (t: string) => t.split("\n").map((l) => l.trim()).filter(Boolean);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const s = await editSummary(sessionId, {
        key_points: split(draft.key_points),
        action_items: split(draft.action_items),
        caveats: split(draft.caveats),
      });
      setSummary(s);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your edits.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-line bg-card p-5 text-sm text-ink-soft">
        Preparing your summary…
      </div>
    );
  }
  if (error && !summary) {
    return (
      <div role="alert" className="rounded-2xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
        {error}
      </div>
    );
  }
  if (!summary) return null;

  const section = (title: string, lines: string[]) =>
    lines.length > 0 && (
      <div className="mt-4">
        <h4 className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">{title}</h4>
        <ul className="mt-2 space-y-2">
          {lines.map((line, i) => (
            <li key={i} className="flex gap-2.5 text-sm text-ink">
              <span aria-hidden className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" />
              {line}
            </li>
          ))}
        </ul>
      </div>
    );

  return (
    <div className="grad-edge rounded-[20px] bg-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-base font-semibold">Your session summary</h3>
          <p className="mt-1 font-mono text-[11px] text-ink-soft/70">
            {summary.source === "gemini" ? "Drafted with AI" : "Drafted from your conversation"}
            {summary.edited && " · edited by you"}
          </p>
        </div>
        <button
          onClick={() => (editing ? void save() : setEditing(true))}
          disabled={busy}
          className="btn-ghost rounded-xl px-3 py-1.5 text-xs disabled:opacity-50"
        >
          {busy ? "…" : editing ? "Save" : "Edit"}
        </button>
      </div>

      {editing ? (
        <div className="mt-4 space-y-3">
          {(
            [
              ["key_points", "Main points (one per line)"],
              ["action_items", "Next steps (max 5, one per line)"],
              ["caveats", "Keep in mind (one per line)"],
            ] as const
          ).map(([field, label]) => (
            <label key={field} className="block">
              <span className="text-[11px] text-ink-soft">{label}</span>
              <textarea
                value={draft[field]}
                onChange={(e) => setDraft({ ...draft, [field]: e.target.value })}
                rows={3}
                className="mt-1 w-full rounded-xl border border-line-strong bg-card px-3 py-2 text-sm focus:border-accent focus:outline-none"
              />
            </label>
          ))}
          <div className="flex gap-2">
            <button
              onClick={() => void save()}
              disabled={busy}
              className="btn-primary rounded-xl px-4 py-2 text-sm disabled:opacity-50"
            >
              Save changes
            </button>
            <button
              onClick={() => setEditing(false)}
              className="btn-ghost rounded-xl px-4 py-2 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          {section("Main points", summary.key_points)}
          {section("Next steps", summary.action_items)}
          {summary.things_to_try.length > 0 && (
            <div className="mt-4">
              <h4 className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
                Things to try
              </h4>
              <div className="mt-2 grid gap-2">
                {summary.things_to_try.map((t) => (
                  <Link
                    key={t.slug}
                    to={`/explore/${t.slug}`}
                    className="rounded-2xl border border-line bg-paper px-3.5 py-2.5 transition-colors hover:border-accent"
                  >
                    <p className="text-sm font-medium">{t.title}</p>
                    <p className="mt-0.5 text-xs text-ink-soft">{t.short_description}</p>
                  </Link>
                ))}
              </div>
            </div>
          )}
          {section("Keep in mind", summary.caveats)}
        </>
      )}
      {error && (
        <p role="alert" className="mt-3 text-xs text-clay">
          {error}
        </p>
      )}
    </div>
  );
}

// --- Stage A3: feedback both roles (spec section 10.11) ---------------------

function FeedbackForm({ sessionId, onDone }: { sessionId: string; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [helpfulness, setHelpfulness] = useState(4);
  const [feltPitched, setFeltPitched] = useState<FeltPitched>("no");
  const [recommend, setRecommend] = useState(true);
  const [freeText, setFreeText] = useState("");

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await submitFeedback(sessionId, {
        role: "mentee",
        mentee: {
          helpfulness_1_5: helpfulness,
          felt_pitched: feltPitched,
          would_recommend: recommend,
          free_text: freeText.trim() || undefined,
        },
      });
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send feedback.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grad-edge rounded-[20px] bg-card p-5">
      <h3 className="font-display text-base font-semibold">How was this session?</h3>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
          Helpful?
        </span>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setHelpfulness(n)}
            aria-pressed={helpfulness === n}
            className={`h-8 w-8 rounded-full text-sm transition-colors ${
              helpfulness === n
                ? "bg-accent text-white"
                : "border border-line text-ink-soft hover:border-accent"
            }`}
          >
            {n}
          </button>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
          Did it feel like a sales pitch?
        </span>
        {(["no", "unsure", "yes"] as const).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setFeltPitched(v)}
            aria-pressed={feltPitched === v}
            className={`rounded-full border px-3 py-1 text-xs transition-colors ${
              feltPitched === v
                ? "border-accent bg-accent-soft text-accent"
                : "border-line text-ink-soft hover:border-accent"
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
          Would you recommend it?
        </span>
        {[true, false].map((v) => (
          <button
            key={String(v)}
            type="button"
            onClick={() => setRecommend(v)}
            aria-pressed={recommend === v}
            className={`rounded-full border px-3 py-1 text-xs transition-colors ${
              recommend === v
                ? "border-accent bg-accent-soft text-accent"
                : "border-line text-ink-soft hover:border-accent"
            }`}
          >
            {v ? "Yes" : "No"}
          </button>
        ))}
      </div>

      <label className="mt-3 block">
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
          Anything else? (optional)
        </span>
        <textarea
          value={freeText}
          onChange={(e) => setFreeText(e.target.value.slice(0, 2000))}
          rows={2}
          className="mt-1 w-full rounded-xl border border-line-strong bg-paper px-3 py-2 text-sm placeholder:text-ink-soft/50 focus:border-accent focus:outline-none"
          placeholder="Tell us what worked or didn't"
        />
      </label>

      <button
        onClick={() => void submit()}
        disabled={busy}
        className="btn-primary mt-4 rounded-xl px-4 py-2 text-sm disabled:opacity-50"
      >
        {busy ? "…" : "Send feedback"}
      </button>
      {error && (
        <p role="alert" className="mt-2 text-xs text-clay">
          {error}
        </p>
      )}
    </div>
  );
}

function ChatView({ session, onRefresh }: { session: SessionType; onRefresh: () => void }) {
  const [messages, setMessages] = useState<SessionMessage[]>([]);
  const [friendTest, setFriendTest] = useState<FriendTestResult | null>(null);
  const [reveal, setRevealState] = useState<SessionType["reveal"]>(session.reveal);
  const [notice, setNotice] = useState<string | null>(null);
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decision, setDecision] = useState<GuardianDecision | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const active = session.status === "ACTIVE";

  const reload = useCallback(async () => {
    try {
      setMessages((await listMessages(session.id)).items);
      setFriendTest(await getFriendTest(session.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load messages.");
    }
  }, [session.id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    try {
      const sent = await sendMessage(session.id, text);
      setDecision(sent.guardian);
      setDraft("");
      // Follow with the mentor's (simulated) reply so the thread moves.
      if (active && !sent.guardian.ends_session) {
        await requestMentorReply(session.id);
      }
      await reload();
      if (sent.guardian.ends_session) onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send.");
    } finally {
      setBusy(false);
    }
  }

  async function pickStyle(style: "honest" | "salesy" | "subtle") {
    if (busy || !active) return;
    setBusy(true);
    setError(null);
    try {
      const reply = await requestMentorReply(session.id, style);
      setDecision(reply.guardian);
      await reload();
      if (reply.guardian.ends_session) onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not get a reply.");
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    if (busy) return;
    setBusy(true);
    try {
      await endSession(session.id);
      onRefresh();
      navigate("/sessions");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not end the session.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Session header + Guardian rail (spec UI-4). */}
      <div className="grad-edge rounded-[20px] bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-display text-xl font-semibold tracking-tight">
            {session.mentor_pseudonym}
          </h2>
          <span className="rounded-full bg-paper px-2.5 py-1 font-mono text-[11px] uppercase tracking-wider text-ink-soft">
            {session.status.toLowerCase()}
          </span>
        </div>
        {session.intent_summary && (
          <p className="mt-1.5 text-sm text-ink-soft">“{session.intent_summary}”</p>
        )}
        <p className="mt-2 font-mono text-[11px] text-ink-soft/70">{SIM_BANNER}</p>

        {/* Guardian rail: strikes as ●●○ plus honest counters, never text. */}
        <div className="mt-4 rounded-2xl bg-paper p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
              Guardian
            </p>
            <div className="flex items-center gap-2" title={`Strikes: ${session.guardian.strikes}/3`}>
              <span className="font-mono text-[11px] text-ink-soft">
                strikes {session.guardian.strikes}/3
              </span>
              <span aria-hidden="true" className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className={`h-2 w-2 rounded-full ${
                      i < session.guardian.strikes ? "bg-clay" : "bg-line-strong"
                    }`}
                  />
                ))}
              </span>
            </div>
          </div>
          <p className="mt-2 text-xs text-ink-soft">
            {session.guardian.messages_checked} messages checked ·{" "}
            {session.guardian.pitches_flagged} flagged
            {session.guardian.max_severity > 0 &&
              ` · max severity ${session.guardian.max_severity}`}
          </p>
        </div>

        {/* Simulator style lever — a demo control, clearly not user content. */}
        {active && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-ink-soft">
              Demo · mentor voice:
            </span>
            {(["honest", "salesy", "subtle"] as const).map((style) => (
              <button
                key={style}
                type="button"
                onClick={() => pickStyle(style)}
                disabled={busy}
                className="rounded-full border border-line px-3 py-1 text-[11px] text-ink-soft transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
              >
                {style}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex max-h-[52vh] min-h-[220px] flex-col gap-3 overflow-y-auto rounded-[20px] border border-line bg-paper p-4">
        {messages.length === 0 ? (
          <p className="m-auto text-sm text-ink-soft">
            Say hello and describe what you'd like advice on.
          </p>
        ) : (
          messages.map((m) => <Bubble key={m.id} message={m} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Guardian decision notice — the sender always learns the outcome. */}
      {decision && decision.action !== "ALLOW" && (
        <div
          role="status"
          className={`flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm ${
            decision.action === "BLOCK_AND_REDACT"
              ? "border border-clay/40 bg-clay-soft text-clay"
              : "bg-warm-soft text-warm"
          }`}
        >
          <GuardianGlyph action={decision.action} />
          <span>
            {decision.action === "BLOCK_AND_REDACT"
              ? "Your message was removed: it looked like promotion or contact details. Mentors can't sell here."
              : "Heads up: your message was tagged as possible promotion."}
          </span>
        </div>
      )}

      {friendTest && <FriendTestPanel result={friendTest} />}

      {/* Stage A3: mutual-consent reveal — available while the session runs. */}
      <RevealPanel
        sessionId={session.id}
        reveal={reveal}
        onDone={(r) => {
          setRevealState({
            mentee_consent: r.state === "REVEALED",
            mentor_consent: r.state === "REVEALED",
            revealed_at: r.revealed ? new Date().toISOString() : null,
          });
          setNotice(r.notice);
        }}
      />
      {notice && (
        <p role="status" className="rounded-xl bg-warm/20 px-4 py-2.5 text-xs text-ink-soft">
          {notice}
        </p>
      )}

      {error && (
        <div role="alert" className="rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
          {error}
        </div>
      )}

      {/* Composer */}
      {active ? (
        <form onSubmit={submit} className="flex gap-2">
          <label htmlFor="chat-input" className="sr-only">
            Write a message
          </label>
          <textarea
            id="chat-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value.slice(0, 2000))}
            rows={2}
            placeholder="Ask for advice…"
            className="flex-1 rounded-2xl border border-line-strong bg-card p-3 text-sm placeholder:text-ink-soft/60 focus:border-accent focus:outline-none"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="btn-primary self-end rounded-xl px-5 py-2.5 text-sm disabled:opacity-40"
          >
            {busy ? "…" : "Send"}
          </button>
        </form>
      ) : (
        <p className="rounded-2xl bg-paper px-4 py-3 text-sm text-ink-soft">
          This session has ended.
        </p>
      )}

      {/* Stage A3: once ended — editable summary + feedback (spec 10.8, 10.11). */}
      {!active && (
        <>
          <SummaryPanel sessionId={session.id} />
          {feedbackGiven ? (
            <p className="rounded-2xl bg-accent-soft px-4 py-3 text-sm text-accent">
              Thanks — your feedback was recorded. It helps check the Guardian catches what
              mentees catch.
            </p>
          ) : (
            <FeedbackForm sessionId={session.id} onDone={() => setFeedbackGiven(true)} />
          )}
        </>
      )}

      <div className="flex items-center justify-between">
        <Link to="/sessions" className="text-sm text-ink-soft underline-offset-4 hover:text-accent hover:underline">
          ← All sessions
        </Link>
        {active && (
          <button
            onClick={finish}
            disabled={busy}
            className="btn-ghost rounded-xl px-4 py-2 text-sm disabled:opacity-50"
          >
            End session
          </button>
        )}
      </div>
    </div>
  );
}

function SessionList({ items, onStart }: { items: SessionType[]; onStart: (id: string) => void }) {
  return (
    <div className="space-y-3">
      {items.length === 0 ? (
        <div className="rounded-[20px] border border-dashed border-line-strong bg-card p-10 text-center">
          <p className="text-ink-soft">No sessions yet.</p>
          <Link to="/" className="btn-primary mt-4">
            Describe what you're working through
          </Link>
        </div>
      ) : (
        items.map((s) => (
          <button
            key={s.id}
            onClick={() => onStart(s.id)}
            className="grad-edge w-full rounded-[20px] bg-card p-5 text-left transition-transform hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-display font-semibold">{s.mentor_pseudonym}</h3>
              <span className="rounded-full bg-paper px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-ink-soft">
                {s.status.toLowerCase()}
              </span>
            </div>
            {s.intent_summary && <p className="mt-1 text-sm text-ink-soft">“{s.intent_summary}”</p>}
            <p className="mt-2 font-mono text-[11px] text-ink-soft/70">
              {s.guardian.messages_checked} messages · {s.guardian.pitches_flagged} flagged
            </p>
          </button>
        ))
      )}
    </div>
  );
}

export default function Sessions() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session: auth, signIn, loading } = useSession();
  const [items, setItems] = useState<SessionType[]>([]);
  const [current, setCurrent] = useState<SessionType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const refresh = useCallback(async () => {
    if (!auth) return;
    try {
      setItems((await listSessions()).items);
      if (id) setCurrent(await getSession(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load sessions.");
    }
  }, [auth, id]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Demo: open a session with the first mentor (used by the empty-state CTA).
  async function quickStart() {
    setStarting(true);
    setError(null);
    try {
      const mentorId = (await listMentors({ limit: 1 })).items[0]?.id;
      if (!mentorId) throw new Error("No mentors available.");
      await createSession({ mentor_id: mentorId });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start a session.");
    } finally {
      setStarting(false);
    }
  }

  if (loading) return null;

  // Not signed in — the honest ask, same as the advice flow.
  if (!auth) {
    return (
      <div className="flex min-h-screen flex-col">
        <InnerHeader />
        <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-16">
          <h1 className="font-display text-2xl font-semibold tracking-tight">My sessions</h1>
          <p className="mt-3 max-w-lg text-ink-soft">
            Sessions are private and tied to your made-up name. Sign in to see them.
          </p>
          <button
            onClick={() => signIn("default")}
            disabled={loading}
            className="btn-primary mt-5"
          >
            Continue with a made-up name
          </button>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        {id && current ? (
          <ChatView session={current} onRefresh={refresh} />
        ) : (
          <>
            <div className="mb-6 flex flex-wrap items-center justify-between gap-2">
              <h1 className="font-display text-2xl font-semibold tracking-tight">My sessions</h1>
              <button
                onClick={quickStart}
                disabled={starting}
                className="btn-primary rounded-xl px-4 py-2 text-sm disabled:opacity-50"
              >
                {starting ? "Starting…" : "New session"}
              </button>
            </div>
            {error && (
              <div role="alert" className="mb-4 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay">
                {error}
              </div>
            )}
            <SessionList items={items} onStart={(sid) => navigate(`/sessions/${sid}`)} />
          </>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
