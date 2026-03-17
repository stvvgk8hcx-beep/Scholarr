# Changelog

## [0.2.0] - 2026-03-17

Major feature release: file management overhaul, study tracker, grade weights, history logging, and comprehensive bug fixes.

### Added

#### File Management
- Full file import: upload via drag-and-drop or click-to-browse, linked to academic items
- File rename with disk rename and history entry tracking
- File move between academic items with history entry tracking
- File delete with optional disk removal and history logging
- Metadata panel in library: filename, format, course, item, size, version, import date, path, SHA-256 hash
- File enrichment: all file API responses now include `course_code`, `item_name`, `course_id`
- Course detail Files tab with per-course file listing and upload

#### History / Activity
- Implemented real database queries for history (was returning empty list)
- Grade changes on academic items now create `GradeChange` history entries
- Status changes on academic items now create `StatusChange` history entries
- File operations (import, rename, move, delete) all create history entries
- Course-filtered history via `?course_id=N` parameter
- Event type filtering via `?event_type=Import` (with backward-compatible `action_type` alias)

#### Study Tracker
- Course-aware Pomodoro timer: select a course, track focus time per course
- Session history stored in localStorage with course, duration, task, and date
- Course detail page shows study time stats (today, this week, all time)
- Deep-linking via URL param `?course=ID` auto-selects course
- Course Study Log panel with per-course totals

#### Grade Weights
- Per-course grade weight policy: set default weights by item type (e.g., Exam 40%, Assignment 30%)
- `grade_weights` JSON column on Course model
- Grade weights UI in course Settings tab with live total indicator
- Weight column shown in course detail Items tab

#### Other
- `course_code` field on `AcademicItemResponse` via batch enrichment (`_enrich_items()`)
- Dashboard stat cards now use `/paged` endpoints for accurate total counts
- Global search in topbar navigates to academic items with search filter
- Tag service fully implemented (was all stubs)
- Seed data script (`seed_data.py`) for testing with 6 semesters, 11 courses, 50 items

### Fixed

#### Critical Bugs
- **Activity page crash**: `document.getElementById('filter-entity')` referenced a non-existent element
- **Activity page filter**: API parameter was `action_type` instead of `event_type`
- **History service**: was a stub returning empty list — now queries the database
- **History schema**: fields mismatched DB model (`action_type`/`entity_type` vs `event_type`/`date`)
- **File import service**: was a stub that returned success without saving files
- **Settings export**: `exportDataBackup()` used `event.target` but was called without event parameter
- **Topbar search**: had HTMX attributes pointing at non-existent `#search-results` element
- **Dashboard stats**: used plain list endpoints that don't return `total` counts
- **Dashboard files count**: called non-existent `/api/v1/files/paged` endpoint
- **Course detail Files tab**: showed duplicate of Items tab instead of actual files
- **Academic item creation**: fallback to `course_id=1` when no courses exist now raises clear error

#### Field Naming
- CSV export used `i.title`/`i.item_type` — fixed to `i.name`/`i.type` (academic_items.html, calendar.html)
- Dashboard activity used `ev.description`/`ev.timestamp` — fixed to `ev.event_type`/`ev.date`
- Settings restore used `item.title`/`item.item_type` — fixed to `item.name`/`item.type`

#### Tag Schema
- Tag schema used `name` but DB model uses `label` — aligned to `label`
- Removed `description` field from tag schema (doesn't exist on DB model)

#### UI Consistency
- Removed all emoji characters from UI (replaced with text or SVG icons)
- Replaced emoji sidebar icons with inline SVGs (stroke-based, `currentColor`, 16x16)
- Cloud provider icons in settings now use colored dots instead of emoji
- GPA calculator status uses text instead of checkmark/warning emoji

#### Code Quality
- Moved `json` import in course_service from function-level to module-level
- Removed redundant `select` re-import in academic_item_service
- Library pagination uses named function instead of serialized lambda
- History endpoint accepts both `event_type` (preferred) and `action_type` (backward compat)

### Technical Details

**Tests**: 281 passed, 0 failed
**Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic V2
**Frontend**: Jinja2 templates, Vanilla JS
**Database**: SQLite (dev), MySQL/PostgreSQL (prod)

---

## [0.1.0] - 2026-03-16

First release. Built the whole thing from scratch in Python.

### Added

#### Backend
- FastAPI application with 80+ REST API endpoints across 26 endpoint modules
- SQLAlchemy 2.0 ORM with async support for MySQL and PostgreSQL
- Alembic database migrations (auto-run on startup)
- WebSocket support for real-time updates via SignalR-style ConnectionManager
- File import pipeline: Scan, Parse, Identify, Decide, Organize, Record
- Smart metadata extraction with SHA256 deduplication
- 25+ naming tokens for flexible file organization
- Fuzzy course matching using Levenshtein distance
- API key authentication on all endpoints
- GPA calculator with what-if scenario support
- Calendar event management with iCal generation stubs
- Comprehensive error handling with Sentry integration
- Background task scheduler (APScheduler)
- File system watcher for inbox monitoring (watchdog)
- Mass editor for bulk course/item operations
- Manual import wizard endpoint
- LMS integration stubs (Blackboard, Canvas, Moodle, Google Classroom)
- Word document extraction support (python-docx)
- Cross-platform OS abstraction (DiskProvider, EnvironmentProvider)

#### Frontend
- Pure Python frontend using Jinja2 templates and HTMX
- Sonarr/Radarr-inspired dark theme (~1300 lines of custom CSS)
- 13 page templates: Dashboard, Courses, Course Detail, Add Course, Academic Items,
  Semesters, Calendar, Activity, Library, GPA Calculator, System, Settings, First Run Setup
- Sidebar navigation with section grouping
- Top bar with search, notifications, and user menu
- Toast notification system
- Responsive layout with mobile support
- No JavaScript frameworks — just HTMX for dynamic interactions

#### DevOps & Deployment
- Single-stage Docker build (Python 3.11-slim, no Node.js)
- Docker Compose with MySQL 8.0 for local development and production
- CI/CD workflows with GitHub Actions
- Linux installer (systemd service with MySQL setup)
- macOS installer (LaunchAgent with Homebrew MySQL)
- Windows installer (PowerShell with NSSM service)

### Known Limitations

- Service layer methods are mostly stubs — DB queries need implementation per use case
- File import pipeline processes sequentially (parallelization planned)
- GPA calculation requires numeric grade entries
- LMS integrations are stubs ready for API credentials

---

For setup and usage instructions, see [README.md](README.md).
