# SecureLex UI design rules

- SecureLex is a code editor first, a security analyzer second, and an ML tool third.
- Keep the SecureLex Night palette and Monaco, Inter, and JetBrains Mono. Editor background is `#0D121C`; panel background is `#111826`.
- Blue indicates actions and focus. Severity uses red, orange, yellow, or cyan with an icon and text label. Green means verified, fixed, or safe. Grey is neutral.
- Do not tint whole finding rows by severity. Use a compact marker, icon, and label.
- Section labels are 11 px uppercase and muted; body copy 13 px; finding titles 15 px semibold; metadata 11–12 px; code 14 px. No heading exceeds 16 px.
- Use 4/8/12/16/24 px spacing and 6–8 px radii. Motion lasts 120–150 ms and respects reduced-motion preferences.
- Keep shadows on menus and popovers only. Do not use gradients, glow, decorative animation, or nested cards.
- Keep analysis features one click away; advanced ML detail remains behind its tab.
