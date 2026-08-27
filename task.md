# Implementation Checklist

## 1. Frontend Pages Implementation
- `[x]` Implement `LoginPage.tsx` (Auth logic, UI, routing).
- `[x]` Implement `DashboardPage.tsx` (Metrics overview, recent inspections).
- `[x]` Implement `InspectionsPage.tsx` (List, search, navigation).
- `[x]` Implement `NewInspectionPage.tsx` (Form, error handling).
- `[x]` Implement `InspectionDetailPage.tsx` (Details, status, drag-and-drop image upload).
- `[x]` Update `App.tsx` (Router setup with ProtectedRoute).

## 2. Frontend Polish
- `[x]` Clean up default Vite boilerplate.
- `[x]` Update `index.html` meta tags and title.
- `[x]` Verify successful frontend build via `npm run build`.

## 3. Testing
- `[x]` Create test fixtures (`conftest.py`).
- `[x]` Write auth API tests (`test_auth.py`).
- `[x]` Write inspections API tests (`test_inspections.py`).
- `[x]` Write images API tests (`test_images.py`).
- `[/]` Run automated tests (`pytest`). *Note: Blocked by Python 3.14 environment dependencies.*

## 4. Documentation
- `[x]` Create Root `README.md` (Setup, tech stack, roadmap).
- `[x]` Write `architecture.md` (Diagrams, data flow).
- `[x]` Write `api.md` (Complete endpoint reference).
- `[x]` Write `database.md` (Schema, enums, cascade rules).
- `[x]` Write `development.md` (Contribution guidelines, setup details).

## 5. End-to-End Verification
- `[/]` Backend pip install dependencies. *Note: Blocked by Python 3.14 environment lacking pre-built wheels for `pydantic-core` and rust compiler.*
- `[ ]` Full E2E walk-through.
