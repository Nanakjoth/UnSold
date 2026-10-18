import { useEffect, useState } from "react";
import { fetchConfig } from "../services/api";
import type { AppConfig } from "../types/api";

interface ConfigState {
  config: AppConfig;
  loading: boolean;
}

export function useConfig(): ConfigState {
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    let active = true;
    fetchConfig().then((value) => {
      if (active) setConfig(value);
    });
    return () => {
      active = false;
    };
  }, []);

  return {
    config: config ?? { app_mode: "demo", demo: true, ai_available: false, notice: null },
    loading: config === null,
  };
}
