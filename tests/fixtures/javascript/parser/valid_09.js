import { readFile } from 'fs/promises';
import path from 'path';

export async function loadConfig(filename) {
    const filepath = path.join('/etc', filename);
    return await readFile(filepath, 'utf8');
}
