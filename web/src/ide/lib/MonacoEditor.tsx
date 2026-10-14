import Editor, { loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import { initIDEWorkers } from './monacoWorkers';

// Keep Monaco, its language services and workers in a deferred chunk.  The IDE
// still provides the local Monaco instance, so this stays fully offline.
initIDEWorkers();
loader.config({ monaco });

export default Editor;
