import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as authService from "../services/auth";
import { getToken } from "../services/api";
import type { DeleteSummary, SessionResponse, SessionUpdate } from "../types/api";

interface SessionContextValue {
  session: SessionResponse | null;
  loading: boolean;
  error: string | null;
  signIn: (label?: string) => Promise<void>;
  update: (update: SessionUpdate) => Promise<void>;
  deleteData: () => Promise<DeleteSummary | null>;
  signOut: () => void;
  clearError: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // On mount, if a token already exists, resolve the session it belongs to.
  useEffect(() => {
    let active = true;
    if (!getToken()) {
      setLoading(false);
      return;
    }
    authService
      .getSession()
      .then((value) => {
        if (active) setSession(value);
      })
      .catch(() => {
        // Token invalid/expired — drop it rather than keep a dead session.
        authService.signOut();
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const signIn = useCallback(async (label = "default") => {
    setError(null);
    setLoading(true);
    try {
      setSession(await authService.demoLogin(label));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start a session.");
    } finally {
      setLoading(false);
    }
  }, []);

  const update = useCallback(async (value: SessionUpdate) => {
    setError(null);
    try {
      setSession(await authService.updateSession(value));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not save changes.";
      setError(message);
      throw err;
    }
  }, []);

  const deleteData = useCallback(async (): Promise<DeleteSummary | null> => {
    setError(null);
    try {
      const summary = await authService.deleteMyData();
      setSession(null);
      return summary;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete data.");
      return null;
    }
  }, []);

  const signOut = useCallback(() => {
    authService.signOut();
    setSession(null);
  }, []);

  const value = useMemo(
    () => ({
      session,
      loading,
      error,
      signIn,
      update,
      deleteData,
      signOut,
      clearError: () => setError(null),
    }),
    [session, loading, error, signIn, update, deleteData, signOut],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
}
