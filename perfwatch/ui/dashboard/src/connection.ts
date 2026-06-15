const RECONNECT_DELAYS_MS = [1_000, 2_000, 4_000, 8_000, 10_000];

export function getReconnectDelay(attempt: number): number {
  return RECONNECT_DELAYS_MS[
    Math.min(Math.max(attempt, 0), RECONNECT_DELAYS_MS.length - 1)
  ];
}

export function resolveWebSocketUrl(
  configuredUrl: string,
  pageUrl: URL = new URL(window.location.href),
): string {
  const url = new URL(configuredUrl, pageUrl);

  if (url.protocol === "http:") {
    url.protocol = "ws:";
  } else if (url.protocol === "https:") {
    url.protocol = "wss:";
  }

  return url.toString();
}
