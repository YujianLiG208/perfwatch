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
