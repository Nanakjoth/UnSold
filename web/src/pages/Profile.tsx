import { useState } from "react";
import { Link } from "react-router-dom";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { useSession } from "../hooks/useSession";

const LANGUAGE_OPTIONS = [
  { code: "en", label: "English" },
  { code: "en-IN", label: "English (India)" },
  { code: "hi", label: "Hindi" },
  { code: "es", label: "Spanish" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "pt", label: "Portuguese" },
  { code: "ja", label: "Japanese" },
];

const PRIVACY_POINTS = [
  {
    title: "What others see",
    body: "Nothing — saved interests and feedback are private to your account. Public features that show anything about you arrive with the People stage, and none exist today.",
  },
  {
    title: "What the app stores",
    body: "Your pseudonym, language preference, saved interests, and feedback actions. Feedback reasons are fixed choices, not free text.",
  },
  {
    title: "Honest limits",
    body: "A pseudonym hides you from other members. It does not mean operators or cloud providers can never process technical metadata.",
  },
];

export default function Profile() {
  const { session, loading, error, signIn, update, deleteData, signOut, clearError } =
    useSession();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deletedCount, setDeletedCount] = useState<number | null>(null);

  async function handleSave(patch: Parameters<typeof update>[0]) {
    setSaving(true);
    setSaved(false);
    try {
      await update(patch);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      /* error surfaced via context */
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    const summary = await deleteData();
    setConfirmDelete(false);
    if (summary) setDeletedCount(summary.total);
  }

  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-12">
        {loading && !session ? (
          <div className="card-raised rounded-2xl border border-line bg-card p-10 text-center text-ink-soft">
            Loading your session…
          </div>
        ) : !session ? (
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Your profile</h1>
            <p className="mt-3 max-w-2xl text-ink-soft">
              Sign in to get a made-up name — no email, no password, no real
              identity. That name is what owns your saved interests and feedback.
            </p>
            {deletedCount !== null && (
              <div
                role="status"
                className="mt-6 rounded-xl border border-accent/30 bg-accent-soft px-4 py-3 text-sm text-accent-strong"
              >
                Your data was deleted ({deletedCount} record
                {deletedCount === 1 ? "" : "s"} removed). You're starting fresh.
              </div>
            )}
            {error && (
              <div
                role="alert"
                className="mt-6 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay"
              >
                {error}
              </div>
            )}
            <div className="mt-8 grid gap-5 sm:grid-cols-2">
              <button
                onClick={() => signIn("default")}
                disabled={loading}
                className="card-raised group rounded-2xl border border-line bg-card p-7 text-left transition-all hover:-translate-y-0.5 hover:border-accent disabled:opacity-60"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-accent">
                  <svg
                    viewBox="0 0 24 24"
                    className="h-6 w-6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  >
                    <circle cx="12" cy="8.5" r="3.5" />
                    <path d="M5 20c0-3.6 3.1-6 7-6s7 2.4 7 6" strokeLinecap="round" />
                  </svg>
                </span>
                <h3 className="mt-4 text-lg font-semibold">Sign in with a pseudonym</h3>
                <p className="mt-2 text-sm text-ink-soft">
                  Get a generated name like “calm-heron-482”. It starts a session you
                  can end or delete at any time.
                </p>
                <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-accent">
                  Continue
                  <svg
                    viewBox="0 0 24 24"
                    className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              </button>

              <div className="card-raised rounded-2xl border border-line bg-paper p-7">
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-card text-accent">
                  <svg
                    viewBox="0 0 24 24"
                    className="h-6 w-6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  >
                    <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6l7-3z" strokeLinejoin="round" />
                  </svg>
                </span>
                <h3 className="mt-4 text-lg font-semibold">You can browse first</h3>
                <p className="mt-2 text-sm text-ink-soft">
                  Searching, filtering, and reading every catalogue entry needs no
                  account at all. Save and feedback are the only gated actions.
                </p>
                <Link
                  to="/explore"
                  className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-accent"
                >
                  Explore the catalogue
                  <svg
                    viewBox="0 0 24 24"
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
        ) : (
          <div>
            {/* Identity header */}
            <div className="card-raised flex flex-col gap-4 rounded-2xl border border-line bg-card p-7 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-4">
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent text-xl font-bold uppercase text-white">
                  {session.pseudonym.charAt(0)}
                </span>
                <div>
                  <p className="text-xl font-semibold tracking-tight">{session.pseudonym}</p>
                  <p className="text-sm text-ink-soft">
                    Joined {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {session.is_synthetic && (
                  <span className="rounded-full bg-warm-soft px-3 py-1 text-xs font-semibold text-warm">
                    Synthetic identity
                  </span>
                )}
                <button
                  onClick={signOut}
                  className="rounded-lg border border-line-strong px-3.5 py-2 text-sm font-medium text-ink transition-colors hover:border-accent hover:text-accent"
                >
                  Sign out
                </button>
              </div>
            </div>

            {error && (
              <div
                role="alert"
                className="mt-5 rounded-xl border border-clay/30 bg-clay-soft px-4 py-3 text-sm text-clay"
              >
                {error}{" "}
                <button onClick={clearError} className="font-semibold underline">
                  Dismiss
                </button>
              </div>
            )}
            {saved && (
              <div
                role="status"
                className="mt-5 rounded-xl border border-accent/30 bg-accent-soft px-4 py-3 text-sm text-accent-strong"
              >
                Saved.
              </div>
            )}

            {/* Quick links */}
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/saved"
                className="rounded-xl border border-line-strong px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-accent hover:text-accent"
              >
                Your saved list
              </Link>
              <Link
                to="/explore"
                className="rounded-xl border border-line-strong px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-accent hover:text-accent"
              >
                Explore catalogue
              </Link>
            </div>

            {/* Language */}
            <section className="mt-6 rounded-2xl border border-line bg-card p-7">
              <h2 className="text-lg font-semibold">Language</h2>
              <p className="mt-1 text-sm text-ink-soft">
                Used for how the app talks to you.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {LANGUAGE_OPTIONS.map((option) => {
                  const active = session.language === option.code;
                  return (
                    <button
                      key={option.code}
                      onClick={() => handleSave({ language: option.code })}
                      disabled={saving}
                      aria-pressed={active}
                      className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                        active
                          ? "border-accent bg-accent text-white"
                          : "border-line-strong text-ink hover:border-accent hover:text-accent"
                      }`}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Privacy */}
            <section className="mt-6 rounded-2xl border border-line bg-card p-7">
              <h2 className="text-lg font-semibold">What this profile protects</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                {PRIVACY_POINTS.map((point) => (
                  <div key={point.title} className="rounded-xl bg-paper p-4">
                    <p className="text-sm font-semibold">{point.title}</p>
                    <p className="mt-1.5 text-sm text-ink-soft">{point.body}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Data controls */}
            <section className="mt-6 rounded-2xl border border-line bg-ink p-7 text-white">
              <h2 className="text-lg font-semibold">Your data, your call</h2>
              <p className="mt-1 text-sm text-white/70">
                Deleting removes your profile, saved interests, and feedback — and
                reports exactly what was removed.
              </p>
              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <Link
                  to="/privacy"
                  className="inline-flex min-h-11 items-center justify-center rounded-xl bg-white px-6 py-3 font-semibold text-ink transition-transform hover:-translate-y-0.5"
                >
                  Read the privacy page
                </Link>
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="inline-flex min-h-11 items-center justify-center rounded-xl border border-white/25 px-6 py-3 font-semibold text-white transition-colors hover:border-white/60"
                >
                  Delete my data
                </button>
              </div>
            </section>

            {/* Delete confirmation */}
            {confirmDelete && (
              <div className="mt-5 rounded-2xl border border-clay/40 bg-clay-soft p-6">
                <p className="font-semibold text-clay">Delete everything?</p>
                <p className="mt-1 text-sm text-clay/90">
                  This removes your profile record, saved interests, and feedback. It
                  cannot be undone, and you'll get a fresh pseudonym next time.
                </p>
                <div className="mt-4 flex gap-3">
                  <button
                    onClick={handleDelete}
                    className="rounded-lg bg-clay px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
                  >
                    Yes, delete it
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="rounded-lg border border-clay/40 px-4 py-2 text-sm font-semibold text-clay"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
