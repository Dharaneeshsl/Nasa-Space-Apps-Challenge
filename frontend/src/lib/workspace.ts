import { useEffect, useState } from 'react';

/** Versioned local drafts. Storage failure must never block the research workflow. */
export function useDraft<T>(key: string, fallback: T, validate: (value: unknown) => value is T) {
  const storageKey = `combustionlens:v1:${key}`;
  const [value, setValue] = useState<T>(() => {
    try { const parsed: unknown = JSON.parse(localStorage.getItem(storageKey) || 'null'); return validate(parsed) ? parsed : fallback; }
    catch { return fallback; }
  });
  useEffect(() => { try { localStorage.setItem(storageKey, JSON.stringify(value)); } catch { /* Private mode / storage quota: keep the in-memory draft. */ } }, [storageKey, value]);
  return [value, setValue] as const;
}
