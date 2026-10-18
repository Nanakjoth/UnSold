import { useConfig } from "../hooks/useConfig";

/**
 * The honest provenance chip (spec UI-0 section 6). Every AI-assisted result
 * states which path actually produced it — `gemini` only when a live model
 * ran, never by inference. Never omitted.
 */
export default function ProvenanceChip({
  source,
  context,
}: {
  /** "gemini" when a live model produced this; anything else is a fallback. */
  source: string;
  /** What this result IS, e.g. "interpretation", "ranking", "Guardian check". */
  context: string;
}) {
  const { config } = useConfig();
  const isLive = source === "gemini";

  return (
    <span
      title={
        isLive
          ? `Produced by the ${context} model call.`
          : `No live model is configured — this ${context} used the deterministic fallback.`
      }
      className="inline-flex items-center gap-1.5 rounded-full border border-line bg-paper px-2.5 py-1 font-mono text-[11px] text-ink-soft"
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${isLive ? "bg-accent node-pulse" : "bg-warm"}`}
      />
      {isLive ? `AI · ${context}` : "keyword · fallback"}
      {!isLive && config.app_mode === "demo" && (
        <span aria-hidden="true" className="text-ink-soft/60">
          (no AI configured)
        </span>
      )}
    </span>
  );
}
