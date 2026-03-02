/**
 * Extract a human-readable error message from a Python bridge error.
 *
 * The Python bridge scripts write JSON `{"error": "..."}` to stderr.
 * This helper tries to parse that JSON and pull out the message;
 * otherwise it returns the raw string.
 */
export function parseBridgeError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  try {
    const parsed = JSON.parse(raw);
    if (parsed.error) return parsed.error;
  } catch {
    // not JSON, keep as-is
  }
  return raw;
}
