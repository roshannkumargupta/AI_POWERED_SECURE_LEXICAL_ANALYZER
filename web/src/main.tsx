import React from 'react';
import ReactDOM from 'react-dom/client';

import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/600.css';
import '@fontsource/jetbrains-mono/700.css';
import '@fontsource/material-symbols-outlined';

import './theme/tokens.css';
import './ide/tailwind.css';
import { ThemeProvider } from './theme/theme';
import { AppProvider } from './state/store';
import { IDE } from './ide/IDE';
import { initIDEWorkers } from './ide/lib/monacoWorkers';

// Monaco reads this global while its editor module mounts. Install bundled workers
// before React creates the Editor component so it never falls back to the CDN.
initIDEWorkers();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AppProvider>
        <IDE />
      </AppProvider>
    </ThemeProvider>
  </React.StrictMode>
);
