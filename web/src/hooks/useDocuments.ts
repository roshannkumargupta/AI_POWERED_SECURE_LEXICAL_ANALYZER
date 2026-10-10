import { useState, useRef } from 'react';
import * as monaco from 'monaco-editor';
import { DocItem } from '../model/doc';
import { SampleItem } from '../api/client';
import { processFileForOpen } from '../utils/fileLoader';
import { Action } from '../state/store';

interface UseDocumentsOptions {
  dispatch: React.Dispatch<Action>;
  dirtyRef: React.MutableRefObject<boolean>;
}

export function useDocuments({ dispatch, dirtyRef }: UseDocumentsOptions) {
  const [openDocs, setOpenDocs] = useState<DocItem[]>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const untitledIndexRef = useRef(0);
  const [activeSample, setActiveSample] = useState<SampleItem | null>(null);

  const activeDoc = openDocs.find((doc) => doc.id === activeDocId) || null;

  const activateDoc = (doc: DocItem) => {
    if (doc.id === activeDocId) return;
    setActiveDocId(doc.id);
    dispatch({ type: 'SET_SOURCE', payload: doc.content });
    dispatch({ type: 'SET_FILENAME', payload: doc.name });
    dispatch({ type: 'SET_LANGUAGE', payload: doc.language });
    if (doc.analysis) {
      dispatch({ type: 'SET_ANALYSIS', payload: doc.analysis });
    } else {
      dispatch({ type: 'CLEAR_ANALYSIS' });
    }
  };

  const handleSelectSample = (sample: SampleItem) => {
    setActiveSample(sample);
    const existing = openDocs.find((d) => d.sampleId === sample.id && !d.dirty);
    if (existing) {
      activateDoc(existing);
      return;
    }
    const id = `sample-${sample.id}-${Date.now()}-${untitledIndexRef.current++}`;
    const newDoc: DocItem = {
      id,
      name: sample.filename,
      content: sample.code,
      language: sample.language,
      dirty: false,
      sampleId: sample.id,
      analysis: null,
      resultVersion: -1,
      contentVersion: 0,
      status: 'not analysed',
    };
    setOpenDocs((docs) => [...docs, newDoc]);
    setActiveDocId(id);
    dirtyRef.current = false;
    dispatch({ type: 'SET_SOURCE', payload: sample.code });
    dispatch({ type: 'SET_LANGUAGE', payload: sample.language });
    dispatch({ type: 'SET_FILENAME', payload: sample.filename });
    dispatch({ type: 'CLEAR_ANALYSIS' });
  };

  const handleOpenFileObject = async (file: File, folderPath?: string) => {
    const outcome = await processFileForOpen(file, folderPath);
    if (outcome.isUnsupported) {
      return { unsupported: true };
    }
    if (outcome.error) {
      dispatch({ type: 'ADD_TOAST', payload: { message: outcome.error, type: 'error' } });
      return { error: true };
    }
    if (outcome.warning) {
      dispatch({ type: 'ADD_TOAST', payload: { message: outcome.warning, type: 'warning' } });
    }
    if (outcome.file) {
      const ext = outcome.file.name.toLowerCase().split('.').pop() || '';
      const language =
        ext === 'py'
          ? 'python'
          : ext === 'java'
            ? 'java'
            : ['js', 'jsx', 'mjs', 'cjs'].includes(ext)
              ? 'javascript'
              : ['c', 'h', 'cc', 'cpp', 'cxx', 'hpp'].includes(ext)
                ? 'cpp'
                : 'auto';
      const id = `file-${Date.now()}-${untitledIndexRef.current++}`;
      const newDoc: DocItem = {
        id,
        name: outcome.file.name,
        content: outcome.file.content,
        language,
        dirty: false,
        folderPath: outcome.file.folderPath,
        hasCrlf: outcome.file.hasCrlf,
        analysis: null,
        resultVersion: -1,
        contentVersion: 0,
        status: 'not analysed',
      };
      setOpenDocs((docs) => [...docs, newDoc]);
      setActiveDocId(id);
      dispatch({ type: 'SET_FILENAME', payload: outcome.file.name });
      dispatch({ type: 'SET_SOURCE', payload: outcome.file.content });
      dispatch({ type: 'SET_LANGUAGE', payload: language });
      dispatch({ type: 'CLEAR_ANALYSIS' });
    }
    return { success: true };
  };

  const createNewFile = () => {
    setActiveSample(null);
    dirtyRef.current = false;
    untitledIndexRef.current += 1;
    const name = `untitled-${untitledIndexRef.current}`;
    const id = `new-${Date.now()}-${untitledIndexRef.current}`;
    const newDoc: DocItem = {
      id,
      name,
      content: '',
      language: 'auto',
      dirty: false,
      analysis: null,
      resultVersion: -1,
      contentVersion: 0,
      status: 'not analysed',
    };
    setOpenDocs((docs) => [...docs, newDoc]);
    setActiveDocId(id);
    dispatch({ type: 'SET_SOURCE', payload: '' });
    dispatch({ type: 'SET_FILENAME', payload: name });
    dispatch({ type: 'SET_LANGUAGE', payload: 'auto' });
    dispatch({ type: 'CLEAR_ANALYSIS' });
  };

  const closeCurrentFile = (targetId?: string) => {
    const idToClose = targetId || activeDocId;
    if (!idToClose) return;
    const docToClose = openDocs.find((d) => d.id === idToClose);
    if (!docToClose) return;

    if (docToClose.dirty) {
      const confirmClose = window.confirm(
        `File "${docToClose.name}" has unsaved changes. Close anyway?`
      );
      if (!confirmClose) return;
    }

    try {
      const uri = monaco.Uri.parse(`inmemory://securelex/${encodeURIComponent(docToClose.id)}`);
      monaco.editor.getModel(uri)?.dispose();
    } catch {}

    const remaining = openDocs.filter((d) => d.id !== idToClose);
    setOpenDocs(remaining);
    if (activeDocId === idToClose) {
      if (remaining.length > 0) {
        const nextDoc = remaining[remaining.length - 1];
        activateDoc(nextDoc);
      } else {
        setActiveDocId(null);
        dispatch({ type: 'SET_SOURCE', payload: '' });
        dispatch({ type: 'SET_FILENAME', payload: '' });
        dispatch({ type: 'SET_LANGUAGE', payload: 'auto' });
        dispatch({ type: 'CLEAR_ANALYSIS' });
      }
    }
  };

  return {
    openDocs,
    setOpenDocs,
    activeDocId,
    setActiveDocId,
    activeDoc,
    activeSample,
    setActiveSample,
    activateDoc,
    handleSelectSample,
    handleOpenFileObject,
    createNewFile,
    closeCurrentFile,
  };
}
