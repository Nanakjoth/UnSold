import { useConfig } from "../hooks/useConfig";

/**
 * Visible on every screen while the app runs in demo mode (spec section 11).
 * Hidden automatically in production mode unless synthetic records remain.
 */
export default function DemoBanner() {
  const { config } = useConfig();
  if (!config.demo) return null;

  return (
    <div
      role="status"
      className="border-b border-line bg-warm-soft px-4 py-1.5 text-center font-mono text-[11px] uppercase tracking-wider text-warm"
    >
      {config.notice ?? "Prototype using synthetic data."} Identities are
      synthetic and catalogue entries are labelled sample content.
    </div>
  );
}
