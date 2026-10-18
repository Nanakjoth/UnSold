import { Link } from "react-router-dom";
import type { InterestCard as InterestCardType } from "../types/api";

/**
 * Subtle per-category accents (spec section 5): one soft chip colour per
 * category, restrained enough to stay a warm-neutral interface.
 */
export const CATEGORY_STYLES: Record<string, { chip: string; dot: string }> = {
  "Creative Practices": { chip: "bg-violet-50 text-violet-700", dot: "#7c3aed" },
  "Making & Repair": { chip: "bg-amber-50 text-amber-700", dot: "#b45309" },
  "Nature & Living Systems": { chip: "bg-emerald-50 text-emerald-700", dot: "#047857" },
  "Movement & Play": { chip: "bg-rose-50 text-rose-700", dot: "#be123c" },
  "Music & Sound": { chip: "bg-fuchsia-50 text-fuchsia-700", dot: "#a21caf" },
  "Food & Culture": { chip: "bg-orange-50 text-orange-700", dot: "#c2410c" },
  "Design & Visual Thinking": { chip: "bg-sky-50 text-sky-700", dot: "#0369a1" },
  "Games & Strategy": { chip: "bg-indigo-50 text-indigo-700", dot: "#4338ca" },
  "Science & Everyday Experiments": { chip: "bg-teal-50 text-teal-700", dot: "#0f766e" },
  "Community & Craft": { chip: "bg-pink-50 text-pink-700", dot: "#be185d" },
};

export function CategoryChip({ category }: { category: string }) {
  const style = CATEGORY_STYLES[category];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
        style?.chip ?? "bg-paper-deep text-ink-soft"
      }`}
    >
      <span
        aria-hidden="true"
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: style?.dot ?? "#4c5c6a" }}
      />
      {category}
    </span>
  );
}

function ModeBadges({ card }: { card: InterestCardType }) {
  const labels: string[] = [];
  if (card.solo_or_group.includes("solo")) labels.push("Solo");
  if (card.solo_or_group.includes("group")) labels.push("Group");
  if (card.online_or_in_person.includes("online")) labels.push("Online");
  if (card.online_or_in_person.includes("in_person")) labels.push("In person");
  return (
    <div className="flex flex-wrap gap-1.5 text-[11px] text-ink-soft">
      {labels.map((label) => (
        <span key={label} className="rounded border border-line px-1.5 py-0.5">
          {label}
        </span>
      ))}
    </div>
  );
}

/** Scannable card for lists, search results, and related sections. */
export default function InterestCard({ card }: { card: InterestCardType }) {
  return (
    <Link
      to={`/interests/${card.slug}`}
      className="card-raised group flex flex-col rounded-2xl border border-line bg-card p-5 transition-all hover:-translate-y-0.5 hover:border-line-strong"
    >
      <div className="flex items-start justify-between gap-3">
        <CategoryChip category={card.category} />
        {card.difficulty === "beginner" && (
          <span className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-semibold text-accent-strong">
            Beginner-friendly
          </span>
        )}
      </div>
      <h3 className="mt-3 text-lg font-semibold leading-snug tracking-tight transition-colors group-hover:text-accent">
        {card.title}
      </h3>
      <p className="mt-1.5 line-clamp-3 flex-1 text-sm text-ink-soft">
        {card.short_description}
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-line pt-3">
        {card.time_commitment && (
          <span className="text-[11px] font-medium text-ink-soft">
            {card.time_commitment}
          </span>
        )}
        <ModeBadges card={card} />
      </div>
      {card.is_sample_content && (
        <p className="mt-2 text-[10px] uppercase tracking-wide text-ink-soft/70">
          Sample entry
        </p>
      )}
    </Link>
  );
}
