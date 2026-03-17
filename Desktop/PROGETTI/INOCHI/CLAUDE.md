# Inochi — Project Guidelines

## Design Context

### Users
Mix eterogeneo di decisori aziendali: CEO e founder di PMI che cercano un partner digitale completo, CTO e tech lead che valutano soluzioni software e AI, marketing manager in cerca di performance advertising, e PMI che vogliono creare siti, app e soluzioni digitali per le loro imprese. Contesto d'uso: fase di valutazione e selezione fornitore — devono capire rapidamente cosa offre INOCHI e sentirsi in mani competenti.

### Brand Personality
**Elegante, Affidabile, Innovativo.** Tono professionale ma non corporate. Comunicazione diretta e concreta, senza buzzword vuoti. Il brand parla con autorevolezza tecnica ma resta accessibile. L'obiettivo emotivo principale e' evocare **fiducia e competenza** — il visitatore deve sentirsi in mani sicure, con professionisti che sanno il fatto loro.

### Aesthetic Direction
- **Visual tone**: Dark-first, tech-forward, minimal e pulito. Ispirazione Vercel/Linear — estetica dark sofisticata con animazioni fluide e tipografia forte.
- **Primary color**: Giallo INOCHI (#FFDA00, hsl 49 100% 50%) come accento vibrante su sfondo scuro
- **Palette**: Nero, charcoal, grigi scuri + giallo acceso. Contrasto alto. Whitespace generoso.
- **Typography**: Inter (300-900), gerarchia chiara, tracking stretto per titoli grandi
- **Motion**: Animazioni Framer Motion sottili e purposeful — fade-in stagger, hover transforms, glow effects. Niente animazioni gratuite.
- **Theme**: Dark mode e' l'esperienza principale. Light mode supportato come secondario.
- **Anti-references**: Evitare look corporate/enterprise stile Accenture/Deloitte. Niente layout generici, stock photo, o estetica "agency template".

### Design Principles
1. **Dark elegance over flash** — Lo sfondo scuro e' il palcoscenico, il giallo e' l'accento strategico. Mai troppo giallo, mai troppi colori. La sobrietà comunica competenza.
2. **Motion with purpose** — Ogni animazione deve guidare l'attenzione o dare feedback. Se non ha uno scopo UX, non serve. Rispettare `prefers-reduced-motion`.
3. **Typography-driven hierarchy** — I titoli grandi e bold parlano da soli. Il testo secondario resta discreto. Lo spazio bianco (o nero) e' parte del design.
4. **Accessible by default** — WCAG AA come baseline. Contrasto sufficiente su tutti i temi, navigazione keyboard, alt text, focus visibili. Il design premium non sacrifica l'accessibilita'.
5. **Show, don't decorate** — Preferire interazioni funzionali (glow cards, hover states informativi) a decorazioni pure. Ogni elemento visivo deve comunicare qualcosa.

### Tech Stack Reference
- React 18 + TypeScript + Vite
- Tailwind CSS 3 + shadcn/ui + Radix UI primitives
- Framer Motion per animazioni
- Inter (Google Fonts) come font primario
- CSS variables per theming (light/dark), custom `inochi-*` namespace in Tailwind
- Path alias: `@` → `/src`
- Progetto nella cartella `Sito/`

### SEO Guidelines
- Brand name nei title: "Inochi" (mai "INOCHI SRL", mai "Inochi Srl")
- Posizionamento nazionale — nessun riferimento geografico (no "Milano", "Italia")
- Separatore title: `-` (trattino con spazi)
- Pattern title: `{Keywords Rilevanti} - Inochi`
- Descrizioni: concrete, senza buzzword, keyword-focused
- Config SEO centralizzata in `src/lib/seo.config.ts`
- Pre-rendering HTML via `vite-plugin-seo.ts`
