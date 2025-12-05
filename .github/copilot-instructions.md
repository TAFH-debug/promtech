## Purpose

This project is primarily a Next.js frontend (in `frontend/`) using the App Router, HeroUI component library, Tailwind CSS, and TypeScript. There is a placeholder `backend/main.py` but it is empty — treat backend as not yet implemented unless you find additional services.

## Big Picture
- Frontend: `frontend/app/` (Next.js App Router) is the canonical entrypoint. Pages and layouts live under `app/`.
- Components: shared UI lives in `frontend/components/` (examples: `map-draw.tsx`, `sidebar.tsx`, `primitives.ts`).
- Styling: Tailwind config at `frontend/tailwind.config.js` and global styles in `frontend/styles/globals.css`.
- UI library: Heavy use of `@heroui/*` components (Card, Button, etc.) and `lucide-react` icons.

## Key Patterns & Conventions (project-specific)
- App Router + Client components: Many pages use the app router and opt into client-side behavior with `"use client"` at the top of a file (see `frontend/app/dashboard/page.tsx`).
- Dynamic client-only imports: For components that rely on browser-only APIs (map), use `next/dynamic` with `ssr: false`. Example: Map draw import in `frontend/app/dashboard/page.tsx`.
- HeroUI composition: Prefer `@heroui/card` primitives (`Card`, `CardBody`, `CardHeader`) for card layouts rather than ad-hoc divs.
- Icons: Use `lucide-react` icon components (e.g., `MapPin`, `ShoppingCart`) passed as component values in data structures.

## Build / Dev / Lint commands
- Install deps (npm): `npm install` run from `frontend/`.
- Dev server: `npm run dev` (runs `next dev --turbopack`).
- Build: `npm run build` then `npm start` for production.
- Lint: `npm run lint` (runs `eslint --fix`).

Notes: `frontend/package.json` declares `next@15.x`, React 18.3.x and Tailwind v4. The README mentions Next.js 14; prefer using versions in `package.json` when writing automation or infra.

## Integration points & what to look for
- Client-only map: `frontend/components/map-draw.tsx` is imported dynamically — changes must preserve `ssr: false`.
- Theme provider: `frontend/app/providers.tsx` configures `next-themes` for light/dark mode — align new UI components with theme tokens.
- If you add a backend service, there is currently no established API folder in the frontend; add clear environment variables and CORS rules and reference the backend root `backend/`.

## Testing & CI
- No test framework is present in the repository root or `frontend/` (no `jest`, `vitest`, or `pytest` configs detected). If you add tests, include scripts in `frontend/package.json` and a CI step for `npm run lint` and `npm run build`.

## Debugging tips
- Use `npm run dev` for local debugging. Inspect `next` output for server/SSR vs client issues — dynamic imports with `ssr:false` commonly fix map/browser-only errors.
- Lint autofix: run `npm run lint` before committing to catch common style issues.

## Files to consult when changing UI or routing
- `frontend/app/layout.tsx` and `frontend/app/providers.tsx` — global layout and providers.
- `frontend/app/dashboard/page.tsx` — example dashboard using HeroUI cards and dynamic map import.
- `frontend/components/*` — shared components and UI primitives.
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.js` — dependency, TypeScript and Tailwind settings.

## When to ask for help / missing info
- Backend is empty (`backend/main.py`). If you intend to add a backend, confirm desired framework (FastAPI, Flask) and the expected API surface.
- If CI or deployment scripts are required, indicate target platform (Vercel, Netlify, Docker) so we can add appropriate `vercel.json` or Dockerfiles.

If anything important is missing or you want a different focus (e.g., adding local API mock, tests, or CI), tell me and I will update these instructions.
