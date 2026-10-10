export interface ProcessedFile {
  name: string;
  content: string;
  hasCrlf: boolean;
  folderPath?: string;
}

export interface FileLoadOutcome {
  file?: ProcessedFile;
  error?: string;
  warning?: string;
  isUnsupported?: boolean;
}

const SUPPORTED_EXTENSIONS = new Set([
  'py',
  'java',
  'js',
  'jsx',
  'mjs',
  'cjs',
  'c',
  'h',
  'cc',
  'cpp',
  'cxx',
  'hpp',
]);

async function readFileAsUint8Array(file: File): Promise<Uint8Array> {
  if (typeof file.arrayBuffer === 'function') {
    const buffer = await file.arrayBuffer();
    return new Uint8Array(buffer);
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve(new Uint8Array(reader.result as ArrayBuffer));
    };
    reader.onerror = () => reject(reader.error || new Error('FileReader error'));
    reader.readAsArrayBuffer(file);
  });
}

export async function processFileForOpen(
  file: File,
  folderPath?: string
): Promise<FileLoadOutcome> {
  const ext = file.name.toLowerCase().split('.').pop() || '';
  if (!SUPPORTED_EXTENSIONS.has(ext)) {
    return { isUnsupported: true };
  }

  // Size limit: 512 KB = 524,288 bytes
  if (file.size > 512 * 1024) {
    const sizeKb = Math.round(file.size / 1024);
    return {
      error: `File "${file.name}" exceeds 512 KB limit (${sizeKb} KB) and cannot be opened.`,
    };
  }

  try {
    const uint8 = await readFileAsUint8Array(file);

    // Binary check: search for NUL bytes in first 8 KB or >1% of file
    let nulCount = 0;
    const sampleSize = Math.min(8192, uint8.length);
    for (let i = 0; i < sampleSize; i++) {
      if (uint8[i] === 0) nulCount++;
    }
    if (nulCount > 0) {
      return {
        error: `"${file.name}" appears to be a binary file and cannot be opened.`,
      };
    }

    let text = '';
    let hasWarning: string | undefined;

    // Strict UTF-8 decode
    try {
      const strictDecoder = new TextDecoder('utf-8', { fatal: true });
      text = strictDecoder.decode(uint8);
    } catch {
      // Lenient decode with replacement character U+FFFD
      const lenientDecoder = new TextDecoder('utf-8', { fatal: false });
      text = lenientDecoder.decode(uint8);
      hasWarning = 'Not valid UTF-8: some characters were replaced';
    }

    // Strip BOM (Byte Order Mark U+FEFF)
    if (text.charCodeAt(0) === 0xfeff) {
      text = text.slice(1);
    }

    const hasCrlf = text.includes('\r\n');

    return {
      file: {
        name: file.name,
        content: text,
        hasCrlf,
        folderPath,
      },
      warning: hasWarning,
    };
  } catch (err: any) {
    return {
      error: `Failed to read "${file.name}": ${err.message || 'Unknown error'}`,
    };
  }
}
