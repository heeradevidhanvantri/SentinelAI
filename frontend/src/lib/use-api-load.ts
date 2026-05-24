"use client";

import { useEffect, useState } from "react";
import { ApiError, formatApiError } from "./http";

export function useApiLoad<T>(load: () => Promise<T>, fallbackError: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await load();
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? formatApiError(err, fallbackError)
              : fallbackError
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
    // mount-only fetch; callers pass stable lambdas wrapping api.* calls
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { data, loading, error };
}
