export const MIN_PANEL_HEIGHT = 120;
export const MIN_EDITOR_HEIGHT = 150;

export function clampPanelHeight(requested: number, viewportHeight: number): number {
  const max = Math.max(MIN_PANEL_HEIGHT, viewportHeight - MIN_EDITOR_HEIGHT);
  return Math.max(MIN_PANEL_HEIGHT, Math.min(max, Math.round(requested)));
}
