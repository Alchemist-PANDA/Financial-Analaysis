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

export async function safeFetch(url: string, options: RequestInit = {}) {
  try {
    const method = (options.method || 'GET').toUpperCase();

    // Add default headers for JSON
    const headers = new Headers(options.headers || {});
    if (!headers.has('Accept')) {
      headers.set('Accept', 'application/json');
    }

    // Setting Content-Type on GET/HEAD can trigger CORS preflights (and can break SSE).
    if (method !== 'GET' && method !== 'HEAD' && options.body != null && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const res = await fetch(url, { ...options, headers });
    
    // Log for visibility in DevTools
    console.log(`[API REQUEST] ${method} ${url} -> ${res.status}`);

    const contentType = res.headers.get("content-type") || "";
    const text = await res.text();

    // 🔴 Handle sleeping backend / HTML response
    if (!contentType.includes("application/json")) {
      console.error("[API_ERROR] Expected JSON, got HTML/Text. Response snippet:", text.slice(0, 200));
      
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
    console.error("[NETWORK_ERROR]", err);
    const message = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      error: `Network error: ${message || 'Unknown failure'}`
    };
  }
}
