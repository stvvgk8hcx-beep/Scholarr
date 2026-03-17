# Changelog

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
- CI/CD workflows with GitHub Actions:
  - Multi-platform testing (Ubuntu, Windows, macOS)
  - Linting, type checking, unit tests, coverage
  - Automated Docker image builds
  - PyPI publishing
  - Dependency review and security scanning
- Linux installer (systemd service with MySQL setup)
- macOS installer (LaunchAgent with Homebrew MySQL)
- Windows installer (PowerShell with NSSM service)

### Technical Details

**Backend**: Python 3.11+, FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic V2
**Frontend**: Jinja2, HTMX 1.9.10
**Database**: MySQL 8.0 (default), PostgreSQL (optional)
**Infrastructure**: Docker, systemd/LaunchAgent/Windows Service

### Supported Platforms

- Linux: Ubuntu 20.04+, Debian 11+, Fedora, RHEL, Alpine
- macOS: 11+
- Windows: 10/11 with PowerShell 5.1+

### Known Limitations

- Service layer methods are mostly stubs — DB queries need implementation per use case
- File import pipeline processes sequentially (parallelization planned)
- GPA calculation requires numeric grade entries
- LMS integrations are stubs ready for API credentials

---

For setup and usage instructions, see [README.md](README.md).
