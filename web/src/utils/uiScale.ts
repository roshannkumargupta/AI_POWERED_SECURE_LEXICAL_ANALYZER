export type InterfaceZoom = 0.85 | 1 | 1.15;

export function computeUiScale(
  _width: number,
  _height: number,
  userZoom: InterfaceZoom = 1
): number {
  // Keep CSS-pixel typography and controls at their intended size regardless
  // of monitor resolution. Flex layouts already use the available viewport.
  return userZoom;
}

export function monacoMetrics(scale: number, userZoom: InterfaceZoom = 1) {
  return {
    fontSize: Math.round(12 * scale * userZoom),
    lineHeight: Math.round(24 * scale * userZoom),
  };
}
