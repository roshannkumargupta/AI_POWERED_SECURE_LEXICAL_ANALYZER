import { useEffect, useMemo, useRef, useState } from 'react';
import type { CapabilitiesResponse, SampleItem } from '../../api/client';

type Starter = 'empty' | 'hello' | 'vulnerable';
const helloWorld: Record<string, string> = {
  python: 'def main():\n    print("Hello, world!")\n\nif __name__ == "__main__":\n    main()\n',
  java: 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, world!");\n    }\n}\n',
  javascript: 'function main() {\n  console.log("Hello, world!");\n}\n\nmain();\n',
  cpp: '#include <iostream>\n\nint main() {\n    std::cout << "Hello, world!\\n";\n    return 0;\n}\n',
  c: '#include <stdio.h>\n\nint main(void) {\n    puts("Hello, world!");\n    return 0;\n}\n',
};
const normalize = (value: string) => value.toLowerCase().replace(/c\+\+/g, 'cpp').replace(/^py$/, 'python').replace(/^js$/, 'javascript');
const extension = (filename: string) => filename.slice(filename.lastIndexOf('.')).toLowerCase();

export function NewFileDialog({ open, capabilities, samples, existingNames, nextIndex, onClose, onCreate }: {
  open: boolean; capabilities: CapabilitiesResponse | null; samples: SampleItem[]; existingNames: string[]; nextIndex: number;
  onClose(): void; onCreate(value: { name: string; language: string; source: string }): void;
}) {
  const languages = capabilities?.languages ?? [];
  const initialLanguage = languages[0];
  const [language, setLanguage] = useState(initialLanguage?.id ?? '');
  const [name, setName] = useState('');
  const [starter, setStarter] = useState<Starter>('empty');
  const [error, setError] = useState('');
  const dialogRef = useRef<HTMLElement>(null);
  useEffect(() => { if (open) dialogRef.current?.querySelector<HTMLElement>('input,select,button')?.focus(); }, [open]);
  useEffect(() => { if (open) { setLanguage(initialLanguage?.id ?? ''); let index = nextIndex; const ext = initialLanguage?.extensions[0] ?? '.txt'; while (existingNames.some(item => item.toLocaleLowerCase() === `untitled-${index}${ext}`.toLocaleLowerCase())) index += 1; setName(`untitled-${index}${ext}`); setStarter('empty'); setError(''); } }, [open, nextIndex, initialLanguage?.id, initialLanguage?.extensions, existingNames]);
  const selectedLanguage = languages.find(item => item.id === language);
  const candidates = useMemo(() => samples.filter(sample => normalize(sample.language) === normalize(language) && /security|vulnerable|adversarial|cwe/i.test(`${sample.kind ?? ''} ${sample.category} ${sample.title} ${sample.topic ?? ''}`)), [samples, language]);
  if (!open) return null;
  const updateName = (value: string) => {
    setName(value);
    const ext = extension(value);
    const match = languages.find(item => item.extensions.some(itemExtension => itemExtension.toLowerCase() === ext));
    if (match) setLanguage(match.id);
  };
  const create = () => {
    const clean = name.trim();
    if (!clean || /[\\/]/.test(clean) || clean === '.' || clean === '..') { setError('Enter a file name without folder separators.'); return; }
    if (existingNames.some(item => item.toLocaleLowerCase() === clean.toLocaleLowerCase())) { setError('A file with this name is already open.'); return; }
    if (!selectedLanguage?.extensions.some(item => item.toLowerCase() === extension(clean))) { setError(`Choose an allowed extension for ${selectedLanguage?.name ?? 'this language'}.`); return; }
    let source = '';
    if (starter === 'hello') source = helloWorld[normalize(language)] ?? '';
    if (starter === 'vulnerable') {
      const sample = candidates[0];
      if (!sample) { setError('No vulnerable sample is available for this language.'); return; }
      source = sample.code;
    }
    onCreate({ name: clean, language, source });
  };
  return <div className="ide-overlay" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section ref={dialogRef} className="ide-dialog ide-new-file-dialog" role="dialog" aria-modal="true" aria-label="New File" onKeyDown={event => { if (event.key === 'Escape') onClose(); if (event.key === 'Enter' && (event.target as HTMLElement).tagName !== 'TEXTAREA') create(); if (event.key === 'Tab') { const controls = [...(dialogRef.current?.querySelectorAll<HTMLElement>('input,select,button') ?? [])].filter(item => !item.hasAttribute('disabled')); const first = controls[0]; const last = controls.at(-1); if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); } } }}>
    <header><h2>New File</h2><button type="button" aria-label="Close New File dialog" onClick={onClose}>×</button></header>
    <label>File name<input autoFocus value={name} onChange={event => updateName(event.target.value)} aria-label="File name" /></label>
    <label>Language<select value={language} onChange={event => { const next = languages.find(item => item.id === event.target.value); setLanguage(event.target.value); if (next && selectedLanguage?.extensions.includes(extension(name))) setName(`${name.slice(0, name.lastIndexOf('.'))}${next.extensions[0] ?? ''}`); }} aria-label="New file language">{languages.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
    <label>Starter<select value={starter} onChange={event => setStarter(event.target.value as Starter)} aria-label="Starter content"><option value="empty">Empty</option><option value="hello">Hello world</option><option value="vulnerable">Vulnerable sample</option></select></label>
    {starter === 'vulnerable' && !candidates.length && <p className="ide-tree-message">No vulnerable sample is available for this language.</p>}
    {error && <p role="alert" className="ide-dialog-error">{error}</p>}
    <footer><button type="button" onClick={onClose}>Cancel</button><button type="button" className="primary" onClick={create}>Create</button></footer>
  </section></div>;
}
