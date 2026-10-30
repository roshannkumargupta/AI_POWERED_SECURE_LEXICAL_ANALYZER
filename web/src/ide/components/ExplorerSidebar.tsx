import React, { useState, useEffect, useCallback } from 'react';
import type { SidebarPane } from './ActivityBar';
import type { IDEDocument } from '../state/store';
import {
  apiClient,
  type WorkspaceFileNode,
  type WorkspaceSearchResponse,
  type GitStatusResponse,
} from '../../api/client';

interface ExplorerSidebarProps {
  activePane: SidebarPane;
  width?: number;
  onResizeStart?: (e: React.PointerEvent) => void;
  tree: WorkspaceFileNode[];
  documents: IDEDocument[];
  activeDocId: string | null;
  onSelectDoc: (id: string) => void;
  onOpenFile: (path: string) => void;
  onCreateFile: (path: string) => void;
  onRenameFile: (oldPath: string, newPath: string) => void;
  onDeleteFile: (path: string) => void;
  onRefreshTree: () => void;
  onSearchFocusLine: (line: number, col?: number, length?: number) => void;
  onApplyFix: () => void;
  onRunSwarm: () => void;
  fontSize: number;
  onChangeFontSize: (size: number) => void;
  themeMode?: 'dark' | 'light' | 'system';
  onSelectThemeMode?: (mode: 'dark' | 'light' | 'system') => void;
  wordWrap?: 'on' | 'off';
  onToggleWordWrap?: () => void;
  minimap?: boolean;
  onToggleMinimap?: () => void;
  tabSize?: number;
  onChangeTabSize?: (size: number) => void;
  highlightUnicode?: boolean;
  onToggleHighlightUnicode?: (enabled: boolean) => void;
  autoAnalyze: boolean;
  onToggleAutoAnalyze: (enabled: boolean) => void;
  onResetPanelLayout?: () => void;
  onExportSARIF?: () => void;
  securityCount: number;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
}

function getFileIcon(name: string): { icon: string; color: string } {
  const lower = name.toLowerCase();
  if (
    lower.endsWith('.cpp') ||
    lower.endsWith('.cc') ||
    lower.endsWith('.c') ||
    lower.endsWith('.h') ||
    lower.endsWith('.hpp')
  ) {
    return { icon: 'description', color: 'text-primary' };
  }
  if (lower.endsWith('.py') || lower.endsWith('.pyw')) {
    return { icon: 'terminal', color: 'text-status-warning' };
  }
  if (lower.endsWith('.java')) {
    return { icon: 'coffee', color: 'text-status-error' };
  }
  if (
    lower.endsWith('.js') ||
    lower.endsWith('.jsx') ||
    lower.endsWith('.ts') ||
    lower.endsWith('.tsx')
  ) {
    return { icon: 'javascript', color: 'text-status-success' };
  }
  if (lower.endsWith('.json')) {
    return { icon: 'data_object', color: 'text-status-warning' };
  }
  if (lower.endsWith('.md')) {
    return { icon: 'info', color: 'text-text-muted' };
  }
  return { icon: 'description', color: 'text-text-muted' };
}

export const ExplorerSidebar: React.FC<ExplorerSidebarProps> = ({
  activePane,
  width = 220,
  onResizeStart,
  tree,
  documents,
  activeDocId,
  onOpenFile,
  onCreateFile,
  onRenameFile,
  onDeleteFile,
  onRefreshTree,
  onSearchFocusLine,
  onApplyFix,
  onRunSwarm,
  fontSize,
  onChangeFontSize,
  themeMode = 'dark',
  onSelectThemeMode,
  wordWrap = 'on',
  onToggleWordWrap,
  minimap = true,
  onToggleMinimap,
  tabSize = 4,
  onChangeTabSize,
  highlightUnicode = true,
  onToggleHighlightUnicode,
  autoAnalyze,
  onToggleAutoAnalyze,
  onResetPanelLayout,
  onExportSARIF,
  securityCount,
  onShowToast,
}) => {
  // Explorer Folders & Creation state
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => new Set(['src']));
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [creatingInFolder, setCreatingInFolder] = useState<string>('');
  const [newFileName, setNewFileName] = useState('');
  const [renamingPath, setRenamingPath] = useState<string | null>(null);
  const [renameInput, setRenameInput] = useState('');

  // Real Project Search state
  const [searchQuery, setSearchQuery] = useState('U+FEFF');
  const [replaceQuery, setReplaceQuery] = useState('');
  const [isRegex, setIsRegex] = useState(false);
  const [matchCase, setMatchCase] = useState(false);
  const [matchWholeWord, setMatchWholeWord] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<WorkspaceSearchResponse | null>(null);
  const [collapsedSearchFiles, setCollapsedSearchFiles] = useState<Set<string>>(new Set());

  // Real Git state
  const [gitStatus, setGitStatus] = useState<GitStatusResponse | null>(null);
  const [isLoadingGit, setIsLoadingGit] = useState(false);
  const [gitCommitMsg, setGitCommitMsg] = useState('fix(security): strip invisible Trojan byte');
  const [selectedDiffPath, setSelectedDiffPath] = useState<string | null>(null);
  const [diffText, setDiffText] = useState<string | null>(null);
  const [isCommitting, setIsCommitting] = useState(false);

  // Extensions filter
  const [extensionFilter, setExtensionFilter] = useState('');

  const activeDoc = documents.find((d) => d.id === activeDocId);
  const dirtyPathSet = new Set(documents.filter((d) => d.dirty).map((d) => d.name));

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const handleToggleAllFolders = () => {
    if (expandedFolders.size > 0) {
      setExpandedFolders(new Set());
    } else {
      const allDirs: string[] = [];
      const collectDirs = (nodes: WorkspaceFileNode[]) => {
        nodes.forEach((n) => {
          if (n.type === 'directory') {
            allDirs.push(n.path);
            if (n.children) collectDirs(n.children);
          }
        });
      };
      collectDirs(tree);
      setExpandedFolders(new Set(allDirs));
    }
  };

  const submitCreateFile = () => {
    const trimmed = newFileName.trim();
    if (!trimmed) {
      setIsCreatingFile(false);
      return;
    }
    const fullPath = creatingInFolder ? `${creatingInFolder}/${trimmed}` : trimmed;
    onCreateFile(fullPath);
    setIsCreatingFile(false);
    setNewFileName('');
    setCreatingInFolder('');
  };

  const submitRename = () => {
    if (!renamingPath) return;
    const trimmed = renameInput.trim();
    if (!trimmed) {
      setRenamingPath(null);
      return;
    }
    const parts = renamingPath.split('/');
    parts[parts.length - 1] = trimmed;
    const newPath = parts.join('/');
    onRenameFile(renamingPath, newPath);
    setRenamingPath(null);
    setRenameInput('');
  };

  // Real Project-Wide Search
  const handlePerformSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setIsSearching(true);
    try {
      const res = await apiClient.searchWorkspace(searchQuery, isRegex, matchCase, matchWholeWord);
      setSearchResults(res);
      onShowToast(
        `Found ${res.total_matches} match${res.total_matches === 1 ? '' : 'es'} across ${res.file_count} file${res.file_count === 1 ? '' : 's'}.`,
        res.total_matches > 0 ? 'success' : 'info'
      );
    } catch (err: any) {
      onShowToast(`Search failed: ${err?.message || 'Error'}`, 'error');
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, isRegex, matchCase, matchWholeWord, onShowToast]);

  // Real Project-Wide Replace
  const handlePerformReplace = useCallback(async () => {
    if (!searchQuery.trim()) {
      onShowToast('Enter a search term to replace', 'warning');
      return;
    }
    try {
      const res = await apiClient.replaceWorkspace(searchQuery, replaceQuery, undefined, isRegex, matchCase);
      if (res.success) {
        onShowToast(`Replaced ${res.replacements} occurrence(s) across ${res.updated_files.length} file(s).`, 'success');
        onRefreshTree();
        void handlePerformSearch();
      } else {
        onShowToast('Replacement failed.', 'error');
      }
    } catch (err: any) {
      onShowToast(`Replace error: ${err?.message || 'Error'}`, 'error');
    }
  }, [searchQuery, replaceQuery, isRegex, matchCase, onRefreshTree, handlePerformSearch, onShowToast]);

  // Real Git Status fetch
  const fetchGitStatus = useCallback(async () => {
    setIsLoadingGit(true);
    try {
      const status = await apiClient.getGitStatus();
      setGitStatus(status);
    } catch {
      setGitStatus({ available: false, branch: '', clean: true, files: [], reason: 'Failed to connect to Git service.' });
    } finally {
      setIsLoadingGit(false);
    }
  }, []);

  // Fetch Git diff for a specific file
  const handleViewGitDiff = useCallback(async (path: string) => {
    setSelectedDiffPath(path);
    try {
      const res = await apiClient.getGitDiff(path);
      setDiffText(res.diff);
    } catch {
      setDiffText('Failed to load diff.');
    }
  }, []);

  // Real Git Commit
  const handleGitCommit = useCallback(async () => {
    if (!gitCommitMsg.trim()) {
      onShowToast('Please enter a commit message.', 'warning');
      return;
    }
    setIsCommitting(true);
    try {
      const res = await apiClient.gitCommit(gitCommitMsg.trim());
      if (res.success && res.commit_hash) {
        onShowToast(`Committed [${res.commit_hash}]: ${res.message}`, 'success');
        setGitCommitMsg('');
        setDiffText(null);
        setSelectedDiffPath(null);
        void fetchGitStatus();
      } else {
        onShowToast(`Commit failed: ${res.error || 'Unknown error'}`, 'error');
      }
    } catch (err: any) {
      onShowToast(`Commit failed: ${err?.message || 'Error'}`, 'error');
    } finally {
      setIsCommitting(false);
    }
  }, [gitCommitMsg, fetchGitStatus, onShowToast]);

  // Fetch git status when switching to pane-git
  useEffect(() => {
    if (activePane === 'pane-git') {
      void fetchGitStatus();
    }
  }, [activePane, fetchGitStatus]);

  // Render tree node recursively
  const renderTreeNode = (node: WorkspaceFileNode, depth = 0) => {
    const isDir = node.type === 'directory';
    const isExpanded = expandedFolders.has(node.path);
    const isOpen = documents.some((d) => d.name === node.path);
    const isActive = activeDoc?.name === node.path;
    const isDirty = dirtyPathSet.has(node.path);
    const isMainCpp = node.path === 'src/main.cpp' || node.name === 'main.cpp';

    if (isDir) {
      return (
        <div key={node.path} className="flex flex-col">
          <div
            className="group flex items-center justify-between px-2 py-1 text-text-secondary hover:text-text-primary hover:bg-surface-hover cursor-pointer rounded-xs transition-colors"
            style={{ paddingLeft: `${8 + depth * 12}px` }}
            onClick={() => toggleFolder(node.path)}
          >
            <div className="flex items-center gap-1.5 truncate">
              <span className="material-symbols-outlined text-[14px]">
                {isExpanded ? 'expand_more' : 'chevron_right'}
              </span>
              <span className="material-symbols-outlined text-[16px] text-accent-fix">
                {isExpanded ? 'folder_open' : 'folder'}
              </span>
              <span className="font-medium text-[11px] truncate">{node.name}</span>
            </div>
            <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
              <button
                type="button"
                className="hover:text-text-primary text-text-muted p-0.5 rounded"
                title={`New file in ${node.name}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setCreatingInFolder(node.path);
                  setIsCreatingFile(true);
                  setNewFileName('');
                  setExpandedFolders((prev) => new Set([...prev, node.path]));
                }}
              >
                <span className="material-symbols-outlined text-[12px]">note_add</span>
              </button>
            </div>
          </div>

          {isExpanded && (
            <div className="flex flex-col space-y-0.5">
              {isCreatingFile && creatingInFolder === node.path && (
                <div
                  className="flex items-center gap-1 px-2 py-0.5"
                  style={{ paddingLeft: `${20 + depth * 12}px` }}
                >
                  <span className="material-symbols-outlined text-[14px] text-text-muted">
                    note_add
                  </span>
                  <input
                    autoFocus
                    className="flex-1 bg-surface-deepest border border-primary rounded px-1.5 py-0.5 text-[11px] font-mono text-text-primary outline-none"
                    placeholder="filename.ext"
                    value={newFileName}
                    onChange={(e) => setNewFileName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') submitCreateFile();
                      if (e.key === 'Escape') setIsCreatingFile(false);
                    }}
                    onBlur={submitCreateFile}
                  />
                </div>
              )}
              {node.children && node.children.map((child) => renderTreeNode(child, depth + 1))}
            </div>
          )}
        </div>
      );
    }

    // File Node
    const fileIcon = getFileIcon(node.name);
    const isRenamingThis = renamingPath === node.path;

    return (
      <div
        key={node.path}
        className={`group flex items-center justify-between px-2 py-1 cursor-pointer transition-colors rounded-xs ${
          isActive
            ? 'bg-primary/20 text-text-primary font-semibold border-l-2 border-primary shadow-xs'
            : isOpen
            ? 'text-text-primary hover:bg-surface-hover/80'
            : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
        }`}
        style={{ paddingLeft: `${16 + depth * 12}px` }}
        onClick={() => onOpenFile(node.path)}
      >
        <div className="flex items-center gap-1.5 truncate flex-1 min-w-0">
          <span className={`material-symbols-outlined text-[15px] shrink-0 ${fileIcon.color}`}>
            {fileIcon.icon}
          </span>

          {isRenamingThis ? (
            <input
              autoFocus
              className="flex-1 bg-surface-deepest border border-primary rounded px-1 py-0.2 text-[11px] font-mono text-text-primary outline-none"
              value={renameInput}
              onChange={(e) => setRenameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submitRename();
                if (e.key === 'Escape') setRenamingPath(null);
              }}
              onBlur={submitRename}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span className="font-mono text-[11px] truncate">{node.name}</span>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {isDirty && (
            <span
              className="w-2 h-2 rounded-full bg-primary"
              title="Unsaved changes"
            />
          )}

          {!isRenamingThis && (
            <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
              <button
                type="button"
                className="hover:text-text-primary text-text-muted p-0.5 rounded"
                title="Rename file"
                onClick={(e) => {
                  e.stopPropagation();
                  setRenamingPath(node.path);
                  setRenameInput(node.name);
                }}
              >
                <span className="material-symbols-outlined text-[12px]">edit</span>
              </button>
              {!isMainCpp && (
                <button
                  type="button"
                  className="hover:text-status-error text-text-muted p-0.5 rounded"
                  title="Delete file"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm(`Delete ${node.name}?`)) {
                      onDeleteFile(node.path);
                    }
                  }}
                >
                  <span className="material-symbols-outlined text-[12px]">delete</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Builtin Extensions list
  const BUILTIN_EXTENSIONS = [
    {
      id: 'ext-cpp',
      name: 'ISO C++20 Language Plugin',
      desc: 'ISO/IEC 14882:2020 C++ token scanner, AST parser and include validator.',
      version: 'v2.0.4',
      status: 'Active',
      author: 'SecureLex Core',
    },
    {
      id: 'ext-python',
      name: 'Python 3.12 PEP 538 Plugin',
      desc: 'Structural tokenizer, indentation engine, and AST syntax checker.',
      version: 'v3.12.1',
      status: 'Active',
      author: 'SecureLex Core',
    },
    {
      id: 'ext-java',
      name: 'Java SE 17 Grammar Plugin',
      desc: 'Identifier verifier, lexical scanner, and class structure parser.',
      version: 'v17.0.2',
      status: 'Active',
      author: 'SecureLex Core',
    },
    {
      id: 'ext-js',
      name: 'ECMAScript 2024 Plugin',
      desc: 'JavaScript & TypeScript token analyzer and AST validation engine.',
      version: 'v1.4.0',
      status: 'Active',
      author: 'SecureLex Core',
    },
    {
      id: 'ext-trojan',
      name: 'Trojan Source Security Guard',
      desc: 'CVE-2021-42574 bidirectional Unicode override and zero-width trap scanner.',
      version: 'v2.1.0',
      status: 'Active',
      author: 'DeepMind Science',
    },
    {
      id: 'ext-groq',
      name: 'Groq Cloud Fix Synthesizer',
      desc: 'Fast AI inference engine for verified automated remediation patches.',
      version: 'v1.0.0',
      status: 'Active',
      author: 'Groq Cloud',
    },
  ];

  const filteredExtensions = BUILTIN_EXTENSIONS.filter(
    (ext) =>
      !extensionFilter ||
      ext.name.toLowerCase().includes(extensionFilter.toLowerCase()) ||
      ext.desc.toLowerCase().includes(extensionFilter.toLowerCase())
  );

  return (
    <aside
      className="bg-surface-explorer border-r border-border-primary flex flex-col shrink-0 overflow-hidden z-30 select-none transition-colors relative"
      style={{ width: `${width}px` }}
      id="secondarySidebar"
    >
      {/* Resizer Handle */}
      {onResizeStart && (
        <div
          className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-primary/40 active:bg-primary z-40 transition-colors"
          onPointerDown={onResizeStart}
          title="Drag to resize Explorer"
        />
      )}

      {/* PANE 1: EXPLORER */}
      {activePane === 'pane-explorer' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-explorer">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              EXPLORER
            </span>
            <div className="flex items-center gap-1 text-text-muted">
              <button
                type="button"
                className="hover:text-text-primary p-0.5 rounded transition-colors"
                onClick={() => {
                  setCreatingInFolder('');
                  setIsCreatingFile(true);
                  setNewFileName('');
                }}
                title="New File"
              >
                <span className="material-symbols-outlined text-[14px]">note_add</span>
              </button>
              <button
                type="button"
                className="hover:text-text-primary p-0.5 rounded transition-colors"
                onClick={() => {
                  onRefreshTree();
                  onShowToast('Explorer tree refreshed');
                }}
                title="Refresh"
              >
                <span className="material-symbols-outlined text-[14px]">refresh</span>
              </button>
              <button
                type="button"
                className="hover:text-text-primary p-0.5 rounded transition-colors"
                onClick={handleToggleAllFolders}
                title="Toggle Folders"
              >
                <span className="material-symbols-outlined text-[14px]">unfold_less</span>
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto py-1.5 space-y-0.5">
            <div className="px-2 py-1 flex items-center gap-1 font-bold text-[11px] text-text-secondary uppercase tracking-wider">
              <span className="material-symbols-outlined text-[14px]">expand_more</span>
              <span>SECURELEX-WORKSPACE</span>
            </div>

            {/* Root-level Inline New File Input */}
            {isCreatingFile && creatingInFolder === '' && (
              <div className="flex items-center gap-1 px-3 py-1 bg-surface-deepest/60 border-l-2 border-primary">
                <span className="material-symbols-outlined text-[14px] text-text-muted">
                  note_add
                </span>
                <input
                  autoFocus
                  className="flex-1 bg-surface-deepest border border-primary rounded px-1.5 py-0.5 text-[11px] font-mono text-text-primary outline-none"
                  placeholder="filename.ext"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') submitCreateFile();
                    if (e.key === 'Escape') setIsCreatingFile(false);
                  }}
                  onBlur={submitCreateFile}
                />
              </div>
            )}

            {/* Recursive workspace tree */}
            {tree.length > 0 ? (
              tree.map((node) => renderTreeNode(node, 0))
            ) : (
              <div className="px-3 py-4 text-center text-text-muted text-[11px]">
                <p>Workspace is empty</p>
                <button
                  type="button"
                  className="mt-2 text-primary hover:underline text-[11px]"
                  onClick={() => {
                    setCreatingInFolder('');
                    setIsCreatingFile(true);
                  }}
                >
                  Create a file
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* PANE 2: SEARCH & REPLACE (Real Project-Wide Search) */}
      {activePane === 'pane-search' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-search">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              SEARCH &amp; REPLACE
            </span>
            <button
              type="button"
              className="hover:text-text-primary text-text-muted p-0.5 rounded"
              onClick={() => {
                setSearchQuery('');
                setReplaceQuery('');
                setSearchResults(null);
              }}
              title="Clear"
            >
              <span className="material-symbols-outlined text-[14px]">clear_all</span>
            </button>
          </div>
          <div className="p-2.5 space-y-2 flex-1 overflow-y-auto">
            {/* Search Input & Options */}
            <div className="space-y-1.5">
              <div className="relative flex items-center">
                <input
                  className="w-full bg-surface-deepest border border-border-primary rounded px-2 py-1 pr-16 font-mono text-[11px] text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                  id="searchInput"
                  placeholder="Search (e.g. U+FEFF)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') void handlePerformSearch();
                  }}
                />
                <div className="absolute right-1 flex items-center gap-0.5">
                  <button
                    type="button"
                    className={`px-1 py-0.2 rounded text-[10px] font-mono transition-colors ${
                      matchCase ? 'bg-primary text-white font-bold' : 'text-text-muted hover:text-text-primary'
                    }`}
                    onClick={() => setMatchCase(!matchCase)}
                    title="Match Case"
                  >
                    Aa
                  </button>
                  <button
                    type="button"
                    className={`px-1 py-0.2 rounded text-[10px] font-mono transition-colors ${
                      matchWholeWord ? 'bg-primary text-white font-bold' : 'text-text-muted hover:text-text-primary'
                    }`}
                    onClick={() => setMatchWholeWord(!matchWholeWord)}
                    title="Match Whole Word"
                  >
                    \b
                  </button>
                  <button
                    type="button"
                    className={`px-1 py-0.2 rounded text-[10px] font-mono transition-colors ${
                      isRegex ? 'bg-primary text-white font-bold' : 'text-text-muted hover:text-text-primary'
                    }`}
                    onClick={() => setIsRegex(!isRegex)}
                    title="Use Regular Expression"
                  >
                    .*
                  </button>
                </div>
              </div>

              {/* Replace Input */}
              <input
                className="w-full bg-surface-deepest border border-border-primary rounded px-2 py-1 font-mono text-[11px] text-text-primary placeholder-text-muted outline-none focus:border-primary transition-colors"
                id="replaceInput"
                placeholder="Replace with..."
                value={replaceQuery}
                onChange={(e) => setReplaceQuery(e.target.value)}
              />
            </div>

            {/* Action buttons */}
            <div className="flex gap-1.5">
              <button
                type="button"
                className="flex-1 bg-surface-container hover:bg-surface-hover py-1 rounded text-[11px] font-medium border border-border-subtle text-text-primary transition-colors flex items-center justify-center gap-1"
                onClick={() => void handlePerformSearch()}
                disabled={isSearching}
              >
                <span className="material-symbols-outlined text-[13px]">
                  {isSearching ? 'sync' : 'search'}
                </span>
                <span>{isSearching ? 'Searching...' : 'Find All'}</span>
              </button>
              <button
                type="button"
                className="flex-1 bg-primary text-white hover:bg-primary/90 py-1 rounded text-[11px] font-medium shadow-xs transition-colors flex items-center justify-center gap-1"
                onClick={() => void handlePerformReplace()}
              >
                <span className="material-symbols-outlined text-[13px]">find_replace</span>
                <span>Replace All</span>
              </button>
            </div>

            {/* Search Match Summary */}
            {searchResults && (
              <div
                className="text-[11px] text-text-secondary pt-2 border-t border-border-subtle font-medium flex items-center justify-between"
                id="searchMatchCount"
              >
                <span>
                  {searchResults.total_matches} result{searchResults.total_matches === 1 ? '' : 's'} in{' '}
                  {searchResults.file_count} file{searchResults.file_count === 1 ? '' : 's'}
                </span>
                <span className="text-[10px] text-text-muted font-mono">&quot;{searchResults.query}&quot;</span>
              </div>
            )}

            {/* Search Results Tree */}
            {searchResults && searchResults.results.length > 0 && (
              <div className="space-y-1.5 pt-1">
                {searchResults.results.map((fileRes) => {
                  const isCollapsed = collapsedSearchFiles.has(fileRes.file);
                  return (
                    <div
                      key={fileRes.file}
                      className="bg-surface-deepest/50 border border-border-subtle rounded overflow-hidden"
                    >
                      <div
                        className="px-2 py-1 bg-surface-elevated/70 flex items-center justify-between cursor-pointer hover:bg-surface-hover text-[11px] font-mono text-text-primary"
                        onClick={() => {
                          setCollapsedSearchFiles((prev) => {
                            const next = new Set(prev);
                            if (next.has(fileRes.file)) next.delete(fileRes.file);
                            else next.add(fileRes.file);
                            return next;
                          });
                        }}
                      >
                        <div className="flex items-center gap-1 truncate">
                          <span className="material-symbols-outlined text-[13px] text-text-muted">
                            {isCollapsed ? 'chevron_right' : 'expand_more'}
                          </span>
                          <span className="truncate">{fileRes.file}</span>
                        </div>
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-surface-hover text-text-muted font-bold">
                          {fileRes.matches.length}
                        </span>
                      </div>

                      {!isCollapsed && (
                        <div className="divide-y divide-border-subtle/40">
                          {fileRes.matches.map((m, mIdx) => (
                            <div
                              key={mIdx}
                              className="px-2.5 py-1.5 hover:bg-surface-hover cursor-pointer transition-colors text-[11px] font-mono"
                              onClick={() => {
                                onOpenFile(fileRes.file);
                                onSearchFocusLine(m.line, m.col, m.length);
                              }}
                            >
                              <div className="flex items-center justify-between text-[10px] text-text-muted">
                                <span className="text-primary font-semibold">
                                  Ln {m.line}, Col {m.col}
                                </span>
                              </div>
                              <div className="text-text-secondary truncate mt-0.5">
                                {m.line_text}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {searchResults && searchResults.results.length === 0 && (
              <div className="py-6 text-center text-text-muted text-[11px]">
                No matches found in project workspace.
              </div>
            )}
          </div>
        </div>
      )}

      {/* PANE 3: SOURCE CONTROL (Real Git Integration) */}
      {activePane === 'pane-git' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-git">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              SOURCE CONTROL
            </span>
            <button
              type="button"
              className="hover:text-text-primary text-text-muted p-0.5 rounded transition-colors"
              onClick={() => void fetchGitStatus()}
              disabled={isLoadingGit}
              title="Refresh Git Status"
            >
              <span className="material-symbols-outlined text-[14px]">
                {isLoadingGit ? 'sync' : 'refresh'}
              </span>
            </button>
          </div>
          <div className="p-2.5 space-y-2.5 flex-1 overflow-y-auto">
            {gitStatus?.available ? (
              <>
                {/* Branch info */}
                <div className="flex items-center justify-between px-2 py-1 bg-surface-deepest/60 border border-border-subtle rounded text-[11px]">
                  <div className="flex items-center gap-1.5 text-text-primary font-mono">
                    <span className="material-symbols-outlined text-[14px] text-primary">
                      fork_right
                    </span>
                    <span className="font-semibold">{gitStatus.branch}</span>
                  </div>
                  <span className="text-[10px] text-text-muted">
                    {gitStatus.clean ? 'Clean' : `${gitStatus.files.length} changed`}
                  </span>
                </div>

                {/* Commit Message & Action */}
                <div className="space-y-1.5">
                  <textarea
                    rows={2}
                    className="w-full bg-surface-deepest border border-border-primary rounded px-2 py-1 text-[11px] text-text-primary placeholder-text-muted outline-none focus:border-primary font-sans resize-none"
                    id="gitCommitMsg"
                    placeholder="Commit message (e.g. fix: patch Trojan bypass)"
                    value={gitCommitMsg}
                    onChange={(e) => setGitCommitMsg(e.target.value)}
                  />
                  <button
                    type="button"
                    className="w-full bg-primary hover:bg-primary/90 text-white font-medium py-1.5 rounded text-[11px] flex items-center justify-center gap-1 shadow-xs transition-colors disabled:opacity-60"
                    onClick={() => void handleGitCommit()}
                    disabled={isCommitting || gitStatus.clean}
                  >
                    <span className="material-symbols-outlined text-[14px]">check</span>
                    <span>{isCommitting ? 'Committing...' : `Commit to ${gitStatus.branch}`}</span>
                  </button>
                </div>

                {/* Changed Files List */}
                <div className="space-y-1 pt-1">
                  <div className="text-[10px] uppercase font-bold text-text-muted flex justify-between tracking-wider">
                    <span>CHANGES ({gitStatus.files.length})</span>
                  </div>

                  {gitStatus.files.length > 0 ? (
                    <div className="space-y-1 max-h-56 overflow-y-auto pr-0.5">
                      {gitStatus.files.map((gf) => {
                        const isSelected = selectedDiffPath === gf.path;
                        return (
                          <div
                            key={gf.path}
                            className={`flex items-center justify-between p-1.5 rounded cursor-pointer border transition-colors ${
                              isSelected
                                ? 'bg-primary/15 border-primary/40'
                                : 'bg-surface-elevated hover:bg-surface-hover border-border-subtle'
                            }`}
                            onClick={() => void handleViewGitDiff(gf.path)}
                            title="Click to view diff"
                          >
                            <div className="flex items-center gap-1.5 truncate">
                              <span
                                className={`material-symbols-outlined text-[13px] ${
                                  gf.status === 'M'
                                    ? 'text-status-warning'
                                    : gf.status === 'U'
                                    ? 'text-status-error'
                                    : 'text-status-success'
                                }`}
                              >
                                {gf.status === 'M'
                                  ? 'edit'
                                  : gf.status === 'U'
                                  ? 'help_outline'
                                  : 'add_circle'}
                              </span>
                              <span className="font-mono text-[11px] text-text-primary truncate">
                                {gf.path}
                              </span>
                            </div>
                            <span
                              className={`text-[10px] font-mono font-bold px-1 rounded ${
                                gf.status === 'M'
                                  ? 'text-status-warning bg-status-warning/10'
                                  : gf.status === 'U'
                                  ? 'text-status-error bg-status-error/10'
                                  : 'text-status-success bg-status-success/10'
                              }`}
                            >
                              {gf.status}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="py-4 text-center text-text-muted text-[11px]">
                      Working tree clean. No unstaged or modified files.
                    </div>
                  )}
                </div>

                {/* Unified Diff View if selected */}
                {selectedDiffPath && diffText && (
                  <div className="mt-2 pt-2 border-t border-border-subtle space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-text-muted">
                      <span className="font-semibold text-text-primary truncate">
                        Diff: {selectedDiffPath}
                      </span>
                      <button
                        type="button"
                        className="hover:text-text-primary p-0.5 rounded"
                        onClick={() => {
                          setSelectedDiffPath(null);
                          setDiffText(null);
                        }}
                      >
                        <span className="material-symbols-outlined text-[12px]">close</span>
                      </button>
                    </div>
                    <pre className="bg-surface-editor border border-border-subtle rounded p-2 text-[10px] font-mono overflow-x-auto max-h-48 leading-relaxed">
                      {diffText.split('\n').map((line, i) => {
                        let cls = 'text-text-secondary';
                        if (line.startsWith('+') && !line.startsWith('+++'))
                          cls = 'text-status-success font-semibold bg-status-success/10 block px-0.5';
                        else if (line.startsWith('-') && !line.startsWith('---'))
                          cls = 'text-status-error font-semibold bg-status-error/10 block px-0.5';
                        else if (line.startsWith('@@')) cls = 'text-accent-ai font-semibold';
                        return (
                          <span key={i} className={cls}>
                            {line}
                            {'\n'}
                          </span>
                        );
                      })}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <div className="p-3 bg-surface-deepest/60 border border-border-subtle rounded-lg space-y-2">
                <div className="flex items-center gap-1.5 text-status-warning font-semibold text-[11px]">
                  <span className="material-symbols-outlined text-[16px]">info</span>
                  <span>Git Integration Unavailable</span>
                </div>
                <p className="text-[10px] text-text-secondary leading-relaxed">
                  {gitStatus?.reason ||
                    'No git repository was found in the workspace root, or the git binary is not installed on the system PATH.'}
                </p>
                <button
                  type="button"
                  className="w-full bg-surface-container hover:bg-surface-hover py-1 rounded text-[11px] text-text-primary border border-border-subtle transition-colors"
                  onClick={() => void fetchGitStatus()}
                >
                  Retry Git Check
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* PANE 4: RUN & DEBUG (Honest Sandboxed Execution State) */}
      {activePane === 'pane-debug' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-debug">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              RUN &amp; DEBUG
            </span>
          </div>
          <div className="p-2.5 space-y-3 flex-1 overflow-y-auto">
            {/* Honest Sandbox Lockdown Alert */}
            <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-lg space-y-2">
              <div className="flex items-center gap-1.5 text-status-error font-semibold text-[11px]">
                <span className="material-symbols-outlined text-[16px]">shield</span>
                <span>Execution Sandbox Unavailable</span>
              </div>
              <p className="text-[10px] text-text-secondary leading-relaxed">
                Arbitrary code execution is disabled on this server. No OS-enforced network-isolated execution sandbox (e.g. gVisor, Docker container sandbox, or Linux namespaces) is currently active on the host.
              </p>
              <div className="text-[9px] text-text-muted border-t border-status-error/20 pt-1 font-mono">
                Status: Execution Disabled (Fails Closed)
              </div>
            </div>

            <div>
              <label className="text-[10px] text-text-muted block mb-1 font-semibold uppercase">
                Debug Configuration
              </label>
              <select className="w-full bg-surface-deepest border border-border-primary text-text-primary rounded px-2 py-1 text-[11px] outline-none">
                <option>C++ Lexer (LLVM / Clang)</option>
                <option>Trojan Unicode Fuzzing</option>
                <option>Python AST Inspector</option>
              </select>
            </div>

            {/* Run Button - Safely Disabled */}
            <button
              type="button"
              disabled
              className="w-full bg-surface-container text-text-muted border border-border-subtle py-1.5 rounded text-[11px] font-semibold flex items-center justify-center gap-1 cursor-not-allowed opacity-60 shadow-xs"
              title="Execution disabled: No host execution sandbox available"
            >
              <span className="material-symbols-outlined text-[15px]">play_disabled</span>
              <span>Start Debugging (Disabled)</span>
            </button>

            {/* Security Audit Breakpoints & Traps */}
            <div className="pt-2 border-t border-border-subtle space-y-1.5">
              <div className="text-[10px] font-bold text-text-muted uppercase">
                SECURITY AUDIT TRAPS
              </div>
              <div
                className="flex items-center justify-between p-1.5 rounded bg-surface-elevated border border-status-error/30 cursor-pointer hover:bg-surface-hover transition-colors"
                onClick={() => onSearchFocusLine(6)}
              >
                <div className="flex items-center gap-1.5 text-[11px] text-text-primary font-mono">
                  <span className="material-symbols-outlined text-[13px] text-status-error">
                    radio_button_checked
                  </span>
                  <span>main.cpp:6</span>
                </div>
                <span className="text-[9px] text-status-error font-semibold uppercase">
                  Trojan Trap
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PANE 5: EXTENSIONS (Actual Available Mechanism) */}
      {activePane === 'pane-extensions' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-extensions">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              EXTENSIONS
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-surface-elevated text-text-muted font-bold">
              {filteredExtensions.length} INSTALLED
            </span>
          </div>
          <div className="p-2.5 space-y-2 flex-1 overflow-y-auto">
            <input
              className="w-full bg-surface-deepest border border-border-primary rounded px-2 py-1 text-[11px] text-text-primary placeholder-text-muted outline-none focus:border-primary"
              placeholder="Filter installed extensions..."
              value={extensionFilter}
              onChange={(e) => setExtensionFilter(e.target.value)}
            />

            <div className="space-y-1.5">
              {filteredExtensions.map((ext) => (
                <div
                  key={ext.id}
                  className="p-2 bg-surface-elevated rounded border border-border-subtle shadow-xs space-y-1"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-semibold text-text-primary text-[11px]">{ext.name}</div>
                      <div className="text-[10px] text-text-muted leading-relaxed">{ext.desc}</div>
                    </div>
                    <span className="text-[9px] text-status-success font-semibold px-1.5 py-0.2 rounded bg-status-success/10 shrink-0">
                      {ext.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-[9px] text-text-muted font-mono pt-1 border-t border-border-subtle/50">
                    <span>{ext.version}</span>
                    <span>{ext.author}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-2.5 bg-surface-deepest/50 border border-border-subtle rounded text-[10px] text-text-muted leading-relaxed">
              ℹ️ External extension marketplace is disabled in sandboxed offline mode. Only verified builtin language plugins and rule analyzers are enabled.
            </div>
          </div>
        </div>
      )}

      {/* PANE 6: SECURITY CENTER */}
      {activePane === 'pane-security' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-security">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              SECURITY AUDIT
            </span>
            <span className="px-1.5 py-0.5 rounded bg-status-error text-[9px] font-bold text-white">
              {securityCount > 0 ? `${securityCount} Critical` : '0 Critical'}
            </span>
          </div>
          <div className="p-2.5 space-y-2 flex-1 overflow-y-auto">
            <div
              className="bg-status-error/10 border border-status-error/40 p-2 rounded space-y-1 cursor-pointer hover:bg-status-error/15 transition-colors"
              onClick={() => onSearchFocusLine(6)}
            >
              <div className="flex items-center gap-1 text-status-error font-semibold text-[11px]">
                <span className="material-symbols-outlined text-[15px]">report</span>
                <span>Trojan Source Attack</span>
              </div>
              <div className="text-[10px] text-text-secondary leading-relaxed">
                Invisible U+FEFF character alters loop boundary during tokenization.
              </div>
              <div className="flex justify-between text-[10px] text-text-muted pt-1 border-t border-status-error/20">
                <span>CWE-172</span>
                <span className="text-status-error font-bold">Severity: 9.8</span>
              </div>
            </div>
            <button
              type="button"
              className="w-full bg-accent-fix/20 text-accent-fix hover:bg-accent-fix/30 border border-accent-fix/40 py-1.5 rounded text-[11px] font-semibold flex items-center justify-center gap-1 transition-colors"
              onClick={onApplyFix}
            >
              <span className="material-symbols-outlined text-[14px]">auto_fix_high</span> Auto-Sanitize File
            </button>
            {onExportSARIF && (
              <button
                type="button"
                className="w-full bg-surface-container hover:bg-surface-hover py-1 rounded text-[11px] text-text-secondary border border-border-subtle transition-colors"
                onClick={onExportSARIF}
              >
                Export SARIF Report
              </button>
            )}
          </div>
        </div>
      )}

      {/* PANE 7: PIPELINE SWARM */}
      {activePane === 'pane-pipeline' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-pipeline">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              AGENT PIPELINE
            </span>
          </div>
          <div className="p-2.5 space-y-2 flex-1 overflow-y-auto">
            <div className="space-y-1.5 text-[11px]">
              <div className="p-2 bg-surface-elevated rounded border border-status-success/30 flex justify-between items-center shadow-xs">
                <span className="text-text-primary">1. Lexer Agent</span>
                <span className="text-status-success font-semibold text-[10px]">Ready</span>
              </div>
              <div className="p-2 bg-surface-elevated rounded border border-status-success/30 flex justify-between items-center shadow-xs">
                <span className="text-text-primary">2. Parser Agent</span>
                <span className="text-status-success font-semibold text-[10px]">Ready</span>
              </div>
              <div className="p-2 bg-surface-elevated rounded border border-status-warning/40 flex justify-between items-center shadow-xs">
                <span className="text-text-primary">3. Semantic Agent</span>
                <span className="text-status-warning font-semibold text-[10px]">
                  {securityCount > 0 ? 'Triggered' : 'Clean'}
                </span>
              </div>
              <div className="p-2 bg-surface-elevated rounded border border-border-subtle flex justify-between items-center text-text-muted shadow-xs">
                <span className="text-text-primary">4. Fix Agent</span>
                <span className="text-accent-fix font-semibold text-[10px]">Armed</span>
              </div>
            </div>
            <button
              type="button"
              className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-1.5 rounded text-[11px] mt-2 shadow-xs transition-colors"
              onClick={onRunSwarm}
            >
              Execute Swarm
            </button>
          </div>
        </div>
      )}

      {/* PANE 8: SETTINGS (Real User Preferences) */}
      {activePane === 'pane-settings' && (
        <div className="sidebar-pane flex flex-col h-full" id="pane-settings">
          <div className="h-8 px-2.5 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase tracking-wider text-text-secondary">
              SETTINGS
            </span>
          </div>
          <div className="p-2.5 space-y-3 flex-1 overflow-y-auto text-[11px]">
            {/* Theme Preference */}
            <div>
              <label className="text-text-muted block mb-1 font-semibold uppercase text-[10px]">
                Theme Appearance
              </label>
              <select
                className="w-full bg-surface-deepest border border-border-primary text-text-primary rounded px-2 py-1 outline-none font-sans"
                value={themeMode}
                onChange={(e) => onSelectThemeMode?.(e.target.value as any)}
              >
                <option value="dark">Dark (High Contrast)</option>
                <option value="light">Light (High Contrast)</option>
                <option value="system">System Preference</option>
              </select>
            </div>

            {/* Editor Font Size */}
            <div>
              <label className="text-text-muted block mb-1 font-semibold uppercase text-[10px]">
                Editor Font Size
              </label>
              <select
                className="w-full bg-surface-deepest border border-border-primary text-text-primary rounded px-2 py-1 outline-none"
                id="settingFontSize"
                value={fontSize}
                onChange={(e) => onChangeFontSize(Number(e.target.value))}
              >
                <option value={11}>11px Compact</option>
                <option value={12}>12px Standard</option>
                <option value={13}>13px Default</option>
                <option value={14}>14px Medium</option>
                <option value={15}>15px Large</option>
                <option value={16}>16px Extra Large</option>
              </select>
            </div>

            {/* Word Wrap */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-text-secondary">Word Wrap</span>
              <button
                type="button"
                className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  wordWrap === 'on' ? 'bg-primary text-white' : 'bg-surface-elevated text-text-muted border border-border-subtle'
                }`}
                onClick={onToggleWordWrap}
              >
                {wordWrap === 'on' ? 'ON' : 'OFF'}
              </button>
            </div>

            {/* Minimap */}
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Editor Minimap</span>
              <button
                type="button"
                className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  minimap ? 'bg-primary text-white' : 'bg-surface-elevated text-text-muted border border-border-subtle'
                }`}
                onClick={onToggleMinimap}
              >
                {minimap ? 'ON' : 'OFF'}
              </button>
            </div>

            {/* Tab Size */}
            <div>
              <label className="text-text-muted block mb-1 font-semibold uppercase text-[10px]">
                Tab Size (Indentation)
              </label>
              <select
                className="w-full bg-surface-deepest border border-border-primary text-text-primary rounded px-2 py-1 outline-none"
                value={tabSize}
                onChange={(e) => onChangeTabSize?.(Number(e.target.value))}
              >
                <option value={2}>2 Spaces</option>
                <option value={4}>4 Spaces (Standard)</option>
              </select>
            </div>

            {/* Highlight Unicode Bugs */}
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Highlight Unicode Traps</span>
              <input
                type="checkbox"
                checked={highlightUnicode}
                className="rounded bg-surface-deepest border-border-primary text-primary focus:ring-0"
                onChange={(e) => onToggleHighlightUnicode?.(e.target.checked)}
              />
            </div>

            {/* Auto-Run On Save */}
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">Auto-Analyze On Save</span>
              <input
                type="checkbox"
                checked={autoAnalyze}
                className="rounded bg-surface-deepest border-border-primary text-primary focus:ring-0"
                onChange={(e) => onToggleAutoAnalyze(e.target.checked)}
              />
            </div>

            {/* Reset Panel Preferences */}
            {onResetPanelLayout && (
              <div className="pt-2 border-t border-border-subtle">
                <button
                  type="button"
                  className="w-full bg-surface-container hover:bg-surface-hover py-1.5 rounded border border-border-subtle text-text-primary font-medium transition-colors"
                  onClick={onResetPanelLayout}
                >
                  Reset Panel Layouts
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
};
