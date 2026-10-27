'use client';

import { useCallback, useEffect, useState } from 'react';

export const API = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API}${path}`, { cache: 'no-store', credentials: 'omit', ...options,
      headers: { ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}), ...options.headers } });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error(`Backend tidak dapat dihubungi di ${API}. Periksa layanan API Python dan konfigurasi origin.`);
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error?.fields?.length
    ? `${body.error.message} ${body.error.fields.map(field => `${field.field}: ${field.message}`).join('; ')}`
    : body.error?.message || `Permintaan gagal (${response.status}).`);
  return body;
}

export function useResource(path, interval = 0, keepPrevious = false) {
  const [state, setState] = useState({ path: null, result: null, error: '', loading: true });
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision(value => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    let timer;
    setState(previous => {
      const keep = previous.path === path || (keepPrevious && previous.path?.split('?')[0] === path.split('?')[0]);
      return { path, result: keep ? previous.result : null, error: '', loading: !keep || !previous.result, updating: true };
    });
    async function load() {
      try {
        const result = await api(path, { signal: controller.signal });
        if (!controller.signal.aborted) {
          setState({ path, result, error: '', loading: false, updating: false });
          if (interval && (!result.data?.status || ['queued', 'running'].includes(result.data.status))) {
            timer = setTimeout(load, interval);
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) setState(previous => ({ ...previous, error: error.message, loading: false, updating: false }));
      }
    }
    load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [path, interval, revision, keepPrevious]);
  const keep = keepPrevious && state.path?.split('?')[0] === path.split('?')[0];
  return state.path === path ? { ...state, reload } : { result: keep ? state.result : null, error: '', loading: !keep || !state.result, updating: true, reload };
}
