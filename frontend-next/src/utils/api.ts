/**
 * REAL Fetch Guard implementation based on institutional stability requirements.
 * This prevents the "Unexpected token <" error by validating Content-Type 
 * before parsing JSON and handling Hugging Face sleeping states.
 */
const sanitizeEnv = (value?: string): string => (value || '').replace(/\n/g, '').trim();

const trimTrailingSlash = (value: string): string => value.replace(/\/+$/, '');

const isHuggingFaceSpaceHost = (hostname: string): boolean =>
  hostname === 'hf.space' || hostname.endsWith('.hf.space');

export function getApiBaseUrl(): string {
  const configured = sanitizeEnv(process.env.NEXT_PUBLIC_API_URL);
  if (configured) {
    const trimmedConfigured = trimTrailingSlash(configured);

    if (typeof window !== 'undefined') {
      try {
        const configuredUrl = new URL(trimmedConfigured);
        const currentOrigin = trimTrailingSlash(window.location.origin);
        if (
          isHuggingFaceSpaceHost(configuredUrl.hostname) &&
          trimTrailingSlash(configuredUrl.origin) !== currentOrigin
        ) {
          console.warn(
            `[API] NEXT_PUBLIC_API_URL points to Hugging Face (${configuredUrl.origin}) but frontend origin is ${currentOrigin}. ` +
              `Using same-origin base URL so /api/* routing can proxy reliably.`
          );
          return currentOrigin;
        }
      } catch {
        // If NEXT_PUBLIC_API_URL isn't a valid absolute URL, use it as-is.
      }
    }

    return trimmedConfigured;
  }

  if (typeof window !== 'undefined') {
    return trimTrailingSlash(window.location.origin);
  }

  return 'http://localhost:7860';
}

export function getApiKey(): string {
  return sanitizeEnv(process.env.NEXT_PUBLIC_API_KEY) || 'dev_default_key';
}

export async function safeFetch(url: string, options: RequestInit = {}, maxRetries = 2) {
  let attempt = 0;

  const executeFetch = async (): Promise<any> => {
    try {
      const method = (options.method || 'GET').toUpperCase();
      const apiKey = getApiKey();

      // For GET requests, append api_key as a query parameter fallback
      let finalUrl = url;
      if (method === 'GET' && !url.includes('api_key=')) {
        const urlObj = new URL(url, window.location.origin);
        urlObj.searchParams.set('api_key', apiKey);
        finalUrl = urlObj.toString();
      }

      // Add default headers for JSON
      const headers = new Headers(options.headers || {});
      if (!headers.has('X-API-Key')) {
        headers.set('X-API-Key', apiKey);
      }
      if (!headers.has('Accept')) {
        headers.set('Accept', 'application/json');
      }

      // Setting Content-Type on GET/HEAD can trigger CORS preflights (and can break SSE).
      if (method !== 'GET' && method !== 'HEAD' && options.body != null && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }

      const res = await fetch(finalUrl, { ...options, headers });

      // Log for visibility in DevTools
      console.log(`[API REQUEST] ${method} ${url} -> ${res.status}`);

      const contentType = res.headers.get("content-type") || "";
      const text = await res.text();

      // 🔴 Handle sleeping backend / HTML response
      if (!contentType.includes("application/json")) {
        const lowered = text.toLowerCase();
        const isHtml =
          lowered.includes('<!doctype') ||
          lowered.includes('<html') ||
          lowered.includes('</html>') ||
          contentType.includes('text/html');

        if (
          isHtml &&
          (lowered.includes('hugging face') ||
            lowered.includes('gradio') ||
            lowered.includes('space') ||
            lowered.includes('loading') ||
            lowered.includes('building') ||
            lowered.includes('waking') ||
            lowered.includes('sleep'))
        ) {
          // If it's a cold start/sleeping state, we might want to retry
          if (attempt < maxRetries) {
            attempt++;
            const delay = 5000 * attempt;
            console.warn(`[API] Backend sleeping (attempt ${attempt}/${maxRetries}). Retrying in ${delay}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return executeFetch();
          }

          return {
            success: false,
            error: "Backend is waking up (or rebuilding). Wait ~20 seconds and refresh.",
            isHtml: true,
            status: res.status,
          };
        }

        return {
          success: false,
          error: "Server returned non-JSON response.",
          status: res.status,
        };
      }

      try {
        const data = JSON.parse(text);

        if (!res.ok) {
          const message =
            (data && (data.detail || data.error || data.message)) ||
            `Request failed with HTTP ${res.status}`;

          // 🟢 Handle 503 Cache Miss (Background Warm)
          if (res.status === 503 && attempt < maxRetries && url.includes('/api/analyze')) {
            attempt++;
            console.warn(`[API] Analysis cache miss (attempt ${attempt}/${maxRetries}). Waiting 5s for warm...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
            return executeFetch();
          }

          return {
            success: false,
            error: String(message),
            status: res.status,
            data,
          };
        }

        return {
          success: true,
          data: data,
          status: res.status,
        };
      } catch {
        return {
          success: false,
          error: "Invalid JSON response from server",
          status: res.status,
        };
      }
    } catch (err: unknown) {
      const isAbort = err instanceof Error && err.name === 'AbortError';

      if (isAbort) {
        console.warn(`[API] Request aborted (attempt ${attempt}/${maxRetries})`);
        // If aborted due to timeout but we have retries left, try again
        if (attempt < maxRetries) {
          attempt++;
          console.warn(`[API] Retrying after abort in 2s...`);
          await new Promise(resolve => setTimeout(resolve, 2000));
          return executeFetch();
        }
      }

      console.error("[NETWORK_ERROR]", err);
      const message = err instanceof Error ? err.message : String(err);
      return {
        success: false,
        error: isAbort ? "Request timed out. The analysis is taking longer than expected." : `Network error: ${message || 'Unknown failure'}`
      };
    }
  };

  return executeFetch();
}

/**
 * Wake up the backend by pinging the health endpoint.
 */
export async function wakeupBackend(): Promise<void> {
  const baseUrl = getApiBaseUrl();
  try {
    console.log("[API] Waking up backend...");
    await fetch(`${baseUrl}/health`).catch(() => {});
    await new Promise(resolve => setTimeout(resolve, 2000));
  } catch {
    // Ignore errors for wakeup
  }
}
