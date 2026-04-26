import { useState, useEffect, useCallback } from 'react';
import type { ScoredPR } from '../types';
import { PRCard } from './PRCard';

const API_URL = import.meta.env.VITE_API_URL || '';
const CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID || '';

type AuthState = {
  token: string;
  login: string;
  avatar_url: string;
} | null;

export function LiveMode() {
  const [auth, setAuth] = useState<AuthState>(null);
  const [prUrl, setPrUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ScoredPR | null>(null);
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);

  // Check backend health on mount
  useEffect(() => {
    if (!API_URL) {
      setBackendAvailable(false);
      return;
    }
    fetch(`${API_URL}/health`)
      .then(r => r.ok ? setBackendAvailable(true) : setBackendAvailable(false))
      .catch(() => setBackendAvailable(false));
  }, []);

  // Handle OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code || !API_URL) return;

    // Verify state matches
    const savedState = sessionStorage.getItem('oauth_state');
    if (state !== savedState) return;

    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
    sessionStorage.removeItem('oauth_state');

    // Exchange code for token
    fetch(`${API_URL}/auth/exchange`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state }),
    })
      .then(r => {
        if (!r.ok) throw new Error('OAuth exchange failed');
        return r.json();
      })
      .then(data => {
        setAuth({
          token: data.access_token,
          login: data.login,
          avatar_url: data.avatar_url,
        });
      })
      .catch(() => setError('GitHub authentication failed. Please try again.'));
  }, []);

  const handleConnect = useCallback(() => {
    const state = crypto.randomUUID();
    sessionStorage.setItem('oauth_state', state);
    const redirectUri = window.location.origin + window.location.pathname;
    window.location.href =
      `https://github.com/login/oauth/authorize` +
      `?client_id=${CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&scope=public_repo read:user` +
      `&state=${state}`;
  }, []);

  const handleDisconnect = useCallback(() => {
    setAuth(null);
    setResult(null);
    setError('');
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!auth || !prUrl.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const resp = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`,
        },
        body: JSON.stringify({ pr_url: prUrl.trim() }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `Analysis failed (${resp.status})`);
      }

      const data = await resp.json();
      setResult(data as ScoredPR);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  }, [auth, prUrl]);

  // Backend not configured or unavailable
  if (backendAvailable === false) {
    return (
      <section id="live" className="px-6 py-10 max-w-6xl mx-auto">
        <div className="border border-dashed border-gray-300 rounded-xl p-8 text-center">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            Try any public PR
          </h2>
          <p className="text-sm text-gray-500 max-w-lg mx-auto">
            Live mode is temporarily unavailable. The featured PRs above show
            how it works.
          </p>
        </div>
      </section>
    );
  }

  // Still checking
  if (backendAvailable === null) {
    return (
      <section id="live" className="px-6 py-10 max-w-6xl mx-auto">
        <div className="border border-dashed border-gray-300 rounded-xl p-8 text-center">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Try any public PR
          </h2>
          <p className="text-sm text-gray-500">Checking backend availability...</p>
        </div>
      </section>
    );
  }

  return (
    <section id="live" className="px-6 py-10 max-w-6xl mx-auto">
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Try any public PR
      </h2>

      {!auth ? (
        // Not connected
        <div className="border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-sm text-gray-600 max-w-lg mx-auto mb-4">
            Run this analysis on any public PR. Connect with GitHub to start.
            Your token, your quota, your repos.
          </p>
          <button
            type="button"
            onClick={handleConnect}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            <GitHubIcon className="w-4 h-4" />
            Connect with GitHub
          </button>
        </div>
      ) : (
        // Connected
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-700">
              {auth.avatar_url && (
                <img
                  src={auth.avatar_url}
                  alt=""
                  className="w-5 h-5 rounded-full"
                />
              )}
              <span>Connected as <strong>@{auth.login}</strong></span>
            </div>
            <button
              type="button"
              onClick={handleDisconnect}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              disconnect
            </button>
          </div>

          <div className="flex gap-3">
            <input
              type="url"
              value={prUrl}
              onChange={e => setPrUrl(e.target.value)}
              placeholder="https://github.com/owner/repo/pull/123"
              className="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
            />
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading || !prUrl.trim()}
              className="px-5 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>

          {loading && (
            <div className="text-sm text-gray-500 text-center py-8">
              Cloning repository and running analysis. This can take 30-90 seconds
              for medium-sized repos.
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {result && (
            <div className="border border-gray-200 rounded-xl p-6 shadow-sm">
              <PRCard pr={result} />
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}
