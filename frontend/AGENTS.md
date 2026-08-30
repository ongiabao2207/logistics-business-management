# Frontend Instructions

React frontend for the Logistics Business Management System.

## Architecture

- Use React with Vite.
- Keep business modules under `src/features/`.
- Each feature owns its own pages, components, API wrapper, hooks, and types.
- Shared UI, layout, hooks, constants, and utilities belong under `src/shared/`.
- Cross-cutting browser/service infrastructure belongs under `src/services/`.

## Boundaries

- The frontend calls backend services through public HTTP APIs only.
- Do not read service databases or service-owned cache data.
- Keep feature API calls behind feature-level API modules such as `contractApi.js`.
- Use mock placeholders for services that are not implemented yet.

## Feature Folder Shape

```text
features/<feature>/
  pages/
  components/
  api/
  hooks/
  types/
```

## Development

- Keep pages usable and operational rather than marketing-oriented.
- Prefer small reusable shared components.
- Keep service naming consistent with backend service names.
