import { Link } from "react-router-dom";
import { SiteFooter, Wordmark } from "../components/Shell";
import { CategoryChip } from "../components/InterestCard";
import { useConfig } from "../hooks/useConfig";

const PILLARS = [
  {
    title: "Explore before you commit",
    body: "Browse the whole catalogue without an account. Saving and feedback are the only things that ask you to sign in — with a made-up name, not an email address.",
    icon: (
      <path
        d="M12 2a7 7 0 0 1 7 7c0 5-7 13-7 13S5 14 5 9a7 7 0 0 1 7-7zm0 4.5A2.5 2.5 0 1 0 12 11a2.5 2.5 0 0 0 0-4.5z"
        fill="currentColor"
        stroke="none"
      />
    ),
  },
  {
    title: "Connections you can check",
    body: "Every relationship between two interests — shared material, shared way of thinking, a genuine contrast — is a written record with a reason attached. Not a black-box score.",
    icon: (
      <path
        d="M7 7h4v4H7zM13 13h4v4h-4zM11 9.5h4M9.5 11v4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    ),
  },
  {
    title: "Honest about its AI",
    body: "Search runs on plain keywords today. When a language model is configured, the interface says so — and when it isn't, it says that too, instead of pretending an AI recommended something.",
    icon: (
      <path
        d="M12 3l1.8 4.6L18.5 9l-4.7 1.4L12 15l-1.8-4.6L5.5 9l4.7-1.4zM18 15l.9 2.3 2.3.7-2.3.7L18 21l-.9-2.3-2.3-.7 2.3-.7z"
        fill="currentColor"
        stroke="none"
      />
    ),
  },
  {
    title: "You own your data",
    body: "Your saved interests and feedback belong to you. Delete them from your profile page at any time and the deletion report shows exactly what was removed.",
    icon: (
      <path
        d="M5 7h14M9 7V5h6v2m-8 0l1 13h8l1-13M10 11v6m4-6v6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
];

const STEPS = [
  {
    n: "01",
    title: "Browse a wide catalogue",
    body: "Over eighty curated activities across ten categories — crafts, food, nature, science, community, and more — each with a concrete first step you can take today.",
  },
  {
    n: "02",
    title: "Follow the connections",
    body: "Open any interest to see why it relates to others: shared materials, shared skills, a prerequisite, or an honest contrast. Cross-category links are where surprises live.",
  },
  {
    n: "03",
    title: "Save what fits, dismiss what doesn't",
    body: "Save an interest for later, mark one you already know, or dismiss it. Your choices shape what you see — and a single dismissal never removes something permanently.",
  },
];

/** Sample of catalogue categories shown as product imagery (real data). */
const SAMPLE_CATEGORIES = [
  "Creative Practices",
  "Nature & Living Systems",
  "Food & Culture",
  "Games & Strategy",
  "Science & Everyday Experiments",
  "Community & Craft",
];

export default function Landing() {
  const { config } = useConfig();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-line/80 bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Wordmark />
          <nav aria-label="Main" className="flex items-center gap-6 text-sm">
            <a
              href="#how"
              className="hidden text-ink-soft underline-offset-4 hover:text-accent hover:underline sm:inline"
            >
              How it works
            </a>
            <a
              href="#limits"
              className="hidden text-ink-soft underline-offset-4 hover:text-accent hover:underline sm:inline"
            >
              What this is not
            </a>
            <Link
              to="/explore"
              className="rounded-lg border border-line-strong px-3.5 py-2 font-medium text-ink transition-colors hover:border-accent hover:text-accent"
            >
              Explore
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="hero-wash border-b border-line">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:py-20 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
            <div className="float-in">
              <p className="inline-flex items-center gap-2 rounded-full border border-line-strong bg-card px-3.5 py-1.5 text-xs font-semibold text-ink-soft">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-glow" />
                Free · browse anonymously · no account needed
              </p>
              <h1 className="mt-5 text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.4rem]">
                There's more out there
                <br />
                than you've{" "}
                <span className="bg-gradient-to-r from-accent to-accent-glow bg-clip-text text-transparent">
                  discovered
                </span>
                .
              </h1>
              <p className="mt-6 max-w-xl text-lg text-ink-soft">
                Atlas is a curated atlas of activities and crafts from around the
                world — with honest connections between them. Start from anything
                you already like, and see what sits one step beyond it.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Link
                  to="/explore"
                  className="inline-flex min-h-12 items-center justify-center rounded-xl bg-accent px-7 py-3.5 text-base font-semibold text-white shadow-[0_10px_24px_-12px_rgba(15,107,82,0.7)] transition-all hover:-translate-y-0.5 hover:bg-accent-strong"
                >
                  Start exploring
                </Link>
                <Link
                  to="/saved"
                  className="inline-flex min-h-12 items-center justify-center rounded-xl border border-line-strong bg-card px-7 py-3.5 text-base font-semibold text-ink transition-all hover:-translate-y-0.5 hover:border-accent hover:text-accent"
                >
                  See your saved list
                </Link>
              </div>
              <dl className="mt-10 flex flex-wrap gap-x-10 gap-y-4 text-sm">
                <div>
                  <dt className="text-ink-soft">Catalogue</dt>
                  <dd className="text-lg font-semibold">88 sample entries</dd>
                </div>
                <div>
                  <dt className="text-ink-soft">Relationships mapped</dt>
                  <dd className="text-lg font-semibold">151 explicit links</dd>
                </div>
                <div>
                  <dt className="text-ink-soft">Account needed to browse</dt>
                  <dd className="text-lg font-semibold">None</dd>
                </div>
              </dl>
            </div>

            {/* Category sampler — real catalogue categories as product imagery */}
            <div className="hidden justify-center lg:flex">
              <div
                aria-hidden="true"
                className="card-raised float-in float-in-delay-1 w-full max-w-md rounded-2xl border border-line bg-card p-6"
              >
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <p className="text-sm font-semibold">From the catalogue</p>
                  <span className="rounded-full bg-accent-soft px-2.5 py-1 text-[11px] font-semibold text-accent-strong">
                    Sample content
                  </span>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {SAMPLE_CATEGORIES.map((category) => (
                    <CategoryChip key={category} category={category} />
                  ))}
                </div>
                <div className="mt-5 space-y-3">
                  {[
                    {
                      t: "Cyanotype Printing",
                      b: "Deep-blue sun prints on coated paper — a first exposure takes minutes outdoors.",
                      c: "Creative Practices",
                    },
                    {
                      t: "Vegetable Fermentation",
                      b: "Salt-brine ferments at room temperature: 20 minutes of work, one week of waiting.",
                      c: "Food & Culture",
                    },
                    {
                      t: "Neighbourhood Mapping",
                      b: "Walk one street and map every tree and bench — then see what the map reveals.",
                      c: "Community & Craft",
                    },
                  ].map((item) => (
                    <div key={item.t} className="rounded-xl bg-paper p-3.5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold">{item.t}</p>
                        <span className="text-[10px] text-ink-soft">↗ linked</span>
                      </div>
                      <p className="mt-1 text-xs text-ink-soft">{item.b}</p>
                      <p className="mt-1.5 text-[10px] uppercase tracking-wide text-ink-soft/70">
                        {item.c}
                      </p>
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-center text-[11px] text-ink-soft">
                  Real entries from the sample catalogue ·{" "}
                  {config.ai_available ? "AI search configured" : "keyword search"}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Trust pillars */}
        <section aria-labelledby="pillars" className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
          <div className="max-w-2xl">
            <h2 id="pillars" className="text-3xl font-semibold tracking-tight">
              Built for curiosity, not engagement
            </h2>
            <p className="mt-3 text-ink-soft">
              A discovery tool should widen your world and be honest about how it
              works. Every design choice here answers one question: can you check
              why you're seeing this?
            </p>
          </div>
          <div className="mt-10 grid gap-5 sm:grid-cols-2">
            {PILLARS.map((pillar, index) => (
              <div
                key={pillar.title}
                className={`card-raised group rounded-2xl border border-line bg-card p-6 transition-colors hover:border-line-strong ${
                  index % 2 === 1 ? "sm:mt-8" : ""
                }`}
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-accent transition-transform group-hover:scale-105">
                  <svg viewBox="0 0 24 24" className="h-6 w-6">
                    {pillar.icon}
                  </svg>
                </span>
                <h3 className="mt-4 text-lg font-semibold">{pillar.title}</h3>
                <p className="mt-2 text-sm text-ink-soft">{pillar.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section
          id="how"
          aria-labelledby="how-heading"
          className="dot-texture border-y border-line bg-paper-deep/60"
        >
          <div className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
            <h2 id="how-heading" className="text-3xl font-semibold tracking-tight">
              How discovery works
            </h2>
            <ol className="mt-10 grid gap-5 sm:grid-cols-3">
              {STEPS.map((item) => (
                <li
                  key={item.n}
                  className="card-raised relative rounded-2xl border border-line bg-card p-6"
                >
                  <span className="text-4xl font-semibold text-line-strong">{item.n}</span>
                  <h3 className="mt-3 text-lg font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm text-ink-soft">{item.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Honest limits */}
        <section id="limits" aria-labelledby="limits-heading" className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <h2 id="limits-heading" className="text-3xl font-semibold tracking-tight">
                What this is not
              </h2>
              <p className="mt-4 text-ink-soft">
                Discovery tools are easy to oversell. Here is the honest version,
                before you sign up for anything.
              </p>
            </div>
            <div className="space-y-5">
              {[
                {
                  t: "Not a recommendation engine — yet.",
                  b: "Today's search is deterministic keyword matching, labelled as such in every response. Personalised ranking and AI-assisted intent search arrive in later stages, and the interface will say which one produced a result.",
                },
                {
                  t: "Sample content, honestly labelled.",
                  b: "Every catalogue entry is marked `is_sample_content`. Descriptions avoid invented prices, dates, and safety guarantees — and each entry carries source notes telling you to verify before relying on it.",
                },
                {
                  t: "A pseudonym is not total anonymity.",
                  b: "You browse and save under a made-up name. That hides you from other members, but it does not mean operators or cloud providers can never process technical metadata.",
                },
                {
                  t: "This is a prototype.",
                  b: "The interface is complete for its current stage; People, Communities, and onboarding arrive in later stages and are labelled as in-progress rather than faked. AI features are never simulated.",
                },
              ].map((item) => (
                <div key={item.t} className="rounded-xl border-l-4 border-accent/40 bg-card py-4 pr-4 pl-5">
                  <p className="font-semibold">{item.t}</p>
                  <p className="mt-1 text-sm text-ink-soft">{item.b}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Closing CTA */}
        <section className="border-t border-line bg-ink text-white">
          <div className="mx-auto max-w-6xl px-4 py-16 text-center sm:py-20">
            <h2 className="text-3xl font-semibold tracking-tight">
              There's more out there than you've discovered.
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-white/70">
              Open the catalogue, search for anything, and follow one connection
              you didn't expect. No account required to start.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link
                to="/explore"
                className="inline-flex min-h-12 items-center justify-center rounded-xl bg-white px-7 py-3.5 font-semibold text-ink transition-all hover:-translate-y-0.5"
              >
                Start exploring
              </Link>
              <Link
                to="/about"
                className="inline-flex min-h-12 items-center justify-center rounded-xl border border-white/25 px-7 py-3.5 font-semibold text-white transition-all hover:-translate-y-0.5 hover:border-white/60"
              >
                How Atlas works
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
