export interface Command {
  id: string;
  title: string;
  keybinding?: string;
  enabled: () => boolean;
  run: () => void;
}

export function fuzzyMatch(query: string, target: string): boolean {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) return true;
  const haystack = target.toLocaleLowerCase();
  let cursor = 0;
  for (const char of needle) {
    cursor = haystack.indexOf(char, cursor);
    if (cursor < 0) return false;
    cursor += 1;
  }
  return true;
}

export function searchCommands(commands: Command[], query: string): Command[] {
  return commands.filter(
    (command) => command.enabled() && fuzzyMatch(query, `${command.title} ${command.id}`)
  );
}

export function keybindingMatches(event: KeyboardEvent, binding = ''): boolean {
  const parts = binding
    .toLocaleLowerCase()
    .split('+')
    .map((part) => part.trim());
  if (!parts.length || !binding) return false;
  const key = parts.at(-1);
  const ctrl = parts.includes('ctrl');
  const shift = parts.includes('shift');
  const alt = parts.includes('alt');
  return (
    event.key.toLocaleLowerCase() === key &&
    event.ctrlKey === ctrl &&
    event.metaKey === false &&
    event.shiftKey === shift &&
    event.altKey === alt
  );
}
