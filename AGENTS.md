# AGENTS Instructions

## General
- Use descriptive commit messages.
- Run `npm run build` after changing frontend code.
- Run `python -m py_compile $(git ls-files '*.py')` after changing Python code.

## Frontend
- Use TypeScript with React and Vite.
- Prefer React Query for data fetching and caching.
- Debounce search inputs and reflect filters in the URL.
- Style with Tailwind CSS or CSS Modules, providing visible focus states and keyboard-friendly modals.
- Make user-visible decisions with UI elements like toasts or badges; avoid relying on console logs.
- Do not invent new backend endpoints; use the ones provided by the API.

## Python Service
- Build FastAPI endpoints with async functions.
- Keep modules organized under `app/api`, `app/models`, and `app/services`.
