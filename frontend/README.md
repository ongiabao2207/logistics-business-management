# Logistics Business Management Frontend

Skeleton React frontend for the Logistics Business Management System.

## Stack

- React
- Vite
- React Router
- TanStack Query

## Setup

```bash
npm install
npm run dev
```

Copy `.env.example` to `.env` when local API routing is available.

## Scripts

```bash
npm run dev
npm run build
npm run preview
```

## Structure

Feature modules live in `src/features/` and follow this shape:

```text
pages/
components/
api/
hooks/
types/
```

Shared layout and reusable UI live in `src/shared/`. Cross-cutting HTTP and token helpers live in `src/services/`.
