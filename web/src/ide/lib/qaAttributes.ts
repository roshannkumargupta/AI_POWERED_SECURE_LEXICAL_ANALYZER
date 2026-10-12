const INTERACTIVE = 'button,input,select,textarea,[role="tab"],[role="option"],[role="menuitem"],[role="separator"],[role="switch"],[role="checkbox"]';

function slug(value: string): string {
  return value.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48) || 'control';
}

/** Apply deterministic QA identifiers to interactive UI elements, including lazy panels. */
export function tagInteractiveElements(root: ParentNode): void {
  const occurrences = new Map<string, number>();
  for (const element of root.querySelectorAll<HTMLElement>(INTERACTIVE)) {
    if (element.hasAttribute('data-qa')) continue;
    const label = element.getAttribute('aria-label')
      || element.getAttribute('placeholder')
      || element.textContent?.trim().replace(/\s+/g, ' ')
      || element.getAttribute('title')
      || element.getAttribute('role')
      || element.tagName.toLowerCase();
    const base = `${element.tagName.toLowerCase()}-${slug(label)}`;
    const ordinal = (occurrences.get(base) ?? 0) + 1;
    occurrences.set(base, ordinal);
    element.dataset.qa = ordinal === 1 ? base : `${base}-${ordinal}`;
  }
}

export function observeInteractiveElements(root: HTMLElement): () => void {
  tagInteractiveElements(root);
  const observer = new MutationObserver(() => tagInteractiveElements(root));
  observer.observe(root, { childList: true, subtree: true });
  return () => observer.disconnect();
}
