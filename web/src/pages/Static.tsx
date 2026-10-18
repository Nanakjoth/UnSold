import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { InnerHeader, SiteFooter } from "../components/Shell";
import { useConfig } from "../hooks/useConfig";

function StaticPage({
  title,
  lede,
  children,
}: {
  title: string;
  lede: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <InnerHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-12">
        <Link
          to="/"
          className="text-sm text-ink-soft underline-offset-4 hover:text-accent hover:underline"
        >
          ← Home
        </Link>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-3 text-lg text-ink-soft">{lede}</p>
        <div className="mt-8 space-y-6 leading-relaxed">{children}</div>
      </main>
      <SiteFooter />
    </div>
  );
}

function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-line bg-card p-6">
      <h2 className="text-lg font-semibold">{heading}</h2>
      <div className="mt-2 space-y-3 text-sm text-ink-soft">{children}</div>
    </section>
  );
}

export function About() {
  const { config } = useConfig();
  return (
    <StaticPage
      title="About Atlas"
      lede="A curated atlas of activities and crafts — with honest, inspectable connections between them."
    >
      <Section heading="What Atlas is">
        <p>
          Atlas is a discovery tool: a catalogue of interests and activities, each
          structured so both people and models can read it — what it is, what you
          need, a concrete first step, and how it relates to everything else.
        </p>
        <p>
          The interface is complete for its current stage. Personalised ranking and
          AI-assisted intent search arrive in later stages and will be labelled when
          they do.
        </p>
      </Section>
      <Section heading="How it works today">
        <p>
          Search is deterministic keyword matching over titles, descriptions, tags,
          and materials — labelled “Keyword search” on every results page. When no
          language model is configured, the interface says so instead of implying an
          AI made suggestions.
        </p>
        <p>
          Relationships between interests are explicit records with a type and a
          written reason — shared material, prerequisite, an honest contrast — not a
          hidden similarity score.
        </p>
      </Section>
      <Section heading="Sample content">
        <p>
          Every catalogue entry carries <code className="rounded bg-paper px-1">is_sample_content</code>{" "}
          and source notes. This build runs with{" "}
          <strong className="text-ink">
            {config.ai_available ? "AI search configured" : "keyword search only"}
          </strong>
          .
        </p>
      </Section>
      <Section heading="What Atlas is not">
        <p>
          Not therapy, crisis support, coaching, or a hiring service. Not a social
          network yet — People and Communities are in-progress. Not a source of
          medical, legal, or safety advice: entries deliberately avoid invented
          prices, dates, and safety guarantees.
        </p>
      </Section>
    </StaticPage>
  );
}

export function Privacy() {
  return (
    <StaticPage
      title="Privacy"
      lede="What is stored, what is not, and how to remove it."
    >
      <Section heading="What we store">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong className="text-ink">A pseudonym, not your identity.</strong> Sessions
            are keyed by an anonymous identifier. In demo mode it is derived from a
            local label; there is no email, phone number, or name.
          </li>
          <li>
            <strong className="text-ink">Your saved interests and feedback.</strong>{" "}
            Both are private to your account. No other member can list them.
          </li>
          <li>
            <strong className="text-ink">Feedback reasons are fixed choices</strong> —
            “not relevant”, “too similar”, “not accessible” — never free text, so
            there is nothing to accidentally disclose.
          </li>
          <li>
            <strong className="text-ink">Language preference.</strong> Optional and
            editable.
          </li>
        </ul>
      </Section>
      <Section heading="What we do not store">
        <ul className="list-disc space-y-2 pl-5">
          <li>No real names, emails, or passwords.</li>
          <li>No precise location, employer, or contact details.</li>
          <li>No messages between members (messaging does not exist yet).</li>
          <li>No behavioural ad tracking of any kind.</li>
        </ul>
      </Section>
      <Section heading="Your deletion rights">
        <p>
          Profile → <strong className="text-ink">Delete my data</strong> removes your
          profile record, saved interests, and feedback, and reports the exact
          per-collection counts. Demo data also resets whenever the server restarts.
        </p>
      </Section>
      <Section heading="Honest limits">
        <p>
          A pseudonym hides you from other members. It does not mean operators or
          cloud providers can never process technical metadata such as IP addresses
          in server logs. Analytics, when added, will be aggregate-only and
          documented here first.
        </p>
      </Section>
    </StaticPage>
  );
}

export function Terms() {
  return (
    <StaticPage
      title="Terms"
      lede="Plain-language terms for a prototype."
    >
      <Section heading="This is a prototype">
        <p>
          Atlas is provided as-is for evaluation. Catalogue content is sample
          content, labelled as such. Do not rely on it for safety-critical,
          medical, legal, or financial decisions.
        </p>
      </Section>
      <Section heading="Your conduct">
        <p>
          If you give feedback, use it honestly. Do not attempt to identify other
          members, scrape the catalogue at scale, or use the service to harass
          anyone. Reasonable rate limits are enforced by the API.
        </p>
      </Section>
      <Section heading="Content">
        <p>
          Sample catalogue entries summarise publicly described practices with
          source-conscious wording. Where a practice belongs to a living cultural
          tradition, the entry says to learn from practitioners rather than from the
          summary.
        </p>
      </Section>
      <Section heading="Changes">
        <p>
          These terms will change as the product does. Material changes will be
          noted on this page; the build stage is always visible in the app.
        </p>
      </Section>
    </StaticPage>
  );
}
