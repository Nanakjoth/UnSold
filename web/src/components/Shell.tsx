import { Link, NavLink, useLocation } from "react-router-dom";
import { useSession } from "../hooks/useSession";
import { useTheme } from "../theme";

/** Constellation-node wordmark (spec UI-0: three nodes, one lit accent). */
export function Wordmark() {
  return (
    <Link to="/" className="flex items-center gap-2.5" aria-label="Home">
      <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center">
        <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none">
          <path
            d="M5 18l7-12 7 12"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-ink-soft"
          />
          <circle cx="5" cy="18" r="2.2" className="fill-ink-soft" />
          <circle cx="12" cy="6" r="2.6" className="fill-accent node-pulse" />
          <circle cx="19" cy="18" r="2.2" className="fill-ink-soft" />
        </svg>
      </span>
      <span className="font-display text-lg font-semibold tracking-tight">
        UNSOLD<span className="text-accent">.</span>
      </span>
    </Link>
  );
}

/* Nav per the UI redesign spec: UNSOLD · Sessions · Explore · How it works ·
 * Trust. "How it works" scrolls to the homepage explainer; Trust is the full
 * transparency page. The mentors directory stays secondary (scope freeze —
 * linked from UNSOLD/Explore, never top-level). */
const NAV_ITEMS: Array<{ to: string; label: string; end?: boolean }> = [
  { to: "/", label: "UNSOLD", end: true },
  { to: "/sessions", label: "Sessions" },
  { to: "/explore", label: "Explore" },
  { to: "/#how-it-works", label: "How it works" },
  { to: "/trust", label: "Trust" },
];

export function MainNav() {
  const location = useLocation();
  return (
    <nav aria-label="Main" className="flex items-center gap-0.5 sm:gap-1">
      {NAV_ITEMS.map((item) => {
        const isAnchor = item.to.includes("#");
        // Anchor links live on the homepage; treat them as active only there.
        const active = isAnchor
          ? location.pathname === "/" && location.hash === "#how-it-works"
          : undefined;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            aria-current={active ? "page" : undefined}
            className={({ isActive }) =>
              `rounded-lg px-2.5 py-2 text-sm font-medium transition-colors sm:px-3 ${
                (active ?? isActive)
                  ? "bg-accent-soft text-accent"
                  : "text-ink-soft hover:bg-paper-deep hover:text-ink"
              }`
            }
          >
            {item.label}
          </NavLink>
        );
      })}
    </nav>
  );
}

/** Sun/moon toggle (spec UI-0: theme toggle in the top bar). */
export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
      className="flex h-9 w-9 items-center justify-center rounded-lg border border-line text-ink-soft transition-colors hover:border-accent hover:text-accent"
    >
      {theme === "dark" ? (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      )}
    </button>
  );
}

/** Identity chip: made-up name, or a quiet sign-in prompt. */
export function ProfileMenu() {
  const { session, signIn, signOut, loading } = useSession();
  const location = useLocation();

  if (loading && !session) {
    return <span className="text-sm text-ink-soft">…</span>;
  }

  if (!session) {
    return (
      <button
        onClick={() => signIn("default")}
        className="rounded-lg border border-line-strong px-3.5 py-2 text-sm font-medium text-ink transition-colors hover:border-accent hover:text-accent"
      >
        Sign in
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <Link
        to="/profile"
        className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-ink transition-colors hover:bg-paper-deep"
        aria-current={location.pathname === "/profile" ? "page" : undefined}
        title={session.pseudonym}
      >
        <span
          aria-hidden="true"
          className="flex h-7 w-7 items-center justify-center rounded-full bg-accent-soft text-xs font-bold text-accent"
        >
          {session.pseudonym.charAt(0)}
        </span>
        <span className="hidden max-w-[9rem] truncate font-mono text-xs sm:inline">
          {session.pseudonym}
        </span>
      </Link>
      <button
        onClick={signOut}
        className="hidden rounded-lg px-2 py-1.5 text-sm text-ink-soft transition-colors hover:text-clay sm:block"
      >
        Sign out
      </button>
    </div>
  );
}

/** Top bar used by every page (spec UI-0: ribbon + wordmark + nav + chips). */
export function InnerHeader() {
  return (
    <header className="glass sticky top-0 z-30 border-b border-line">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          <Wordmark />
          {/* Permanent honesty ribbon — it is a prototype whatever the mode. */}
          <span
            className="hidden rounded-full border border-warm/40 bg-warm-soft px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-warm lg:inline"
            title="Every mentor is synthetic; catalogue content is labelled sample content."
          >
            Prototype — synthetic data
          </span>
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <div className="hidden md:block">
            <MainNav />
          </div>
          <ThemeToggle />
          <span className="mx-0.5 hidden h-6 w-px bg-line sm:block" />
          <ProfileMenu />
        </div>
      </div>
      {/* Mobile: primary nav as a bottom tab bar (spec UI-0). */}
      <nav
        aria-label="Main (mobile)"
        className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-card/95 py-1.5 backdrop-blur md:hidden"
      >
        {NAV_ITEMS.filter((item) => !item.to.includes("#")).map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 rounded-lg px-1 py-1.5 text-[11px] font-medium transition-colors ${
                isActive ? "text-accent" : "text-ink-soft"
              }`
            }
          >
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-card">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-ink-soft sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-display font-semibold text-ink">
            UNSOLD<span className="text-accent">.</span>
          </span>{" "}
          — anonymous human guidance, protected by AI.
        </p>
        <div className="flex flex-wrap items-center gap-4">
          <Link to="/about" className="underline decoration-line underline-offset-4 hover:text-accent">
            About
          </Link>
          <Link to="/privacy" className="underline decoration-line underline-offset-4 hover:text-accent">
            Privacy
          </Link>
          <Link to="/terms" className="underline decoration-line underline-offset-4 hover:text-accent">
            Terms
          </Link>
          <Link to="/metrics" className="underline decoration-line underline-offset-4 hover:text-accent">
            Metrics
          </Link>
          <p>
            This is a prototype — mentors are synthetic, not real people.{" "}
            <a className="underline decoration-line underline-offset-4 hover:text-accent" href="/healthz">
              System health
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
