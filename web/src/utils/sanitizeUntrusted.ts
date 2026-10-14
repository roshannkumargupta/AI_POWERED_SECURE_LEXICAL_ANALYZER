/** Remove terminal and invisible formatting controls before copy or report export. */
export function sanitizeUntrustedText(value: string): string {
  return value.replace(
    /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]/gu,
    ''
  );
}
