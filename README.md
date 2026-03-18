# Scholarr

**Self-hosted academic management for students**

Scholarr is a local-first app that keeps your courses, deadlines, files, and grades organised without sending anything to the cloud. It runs on your machine, exposes a clean dark-themed web UI, and offers a full REST API for automation.

---

## Features

### Core
| Feature | Details |
|---------|---------|
| **Course & Semester Management** | Track multiple courses across semesters; auto-assign courses to the active semester |
| **Academic Items** | Assignments, Exams, Quizzes, Projects, Labs, Papers — with due dates, status, grades, and weights |
| **Dashboard** | At-a-glance stats: total courses, active items, upcoming deadlines (colour-coded urgency), grade averages, status breakdown |
| **Activity Log** | Full audit trail of every change — grade changes, status updates, file imports, renames, moves, deletes — filterable by event type and course |

### File Management
| Feature | Details |
|---------|---------|
| **File Library** | Browse all managed files with metadata panel, course/format filters, and search |
| **File Upload** | Drag-and-drop or click-to-browse upload, linked to academic items |
| **File Rename** | Rename files on disk with history tracking (old name, new name, timestamp) |
| **File Move** | Reassign files between academic items with full audit trail |
| **File Metadata** | View filename, format, course, item, size, version, import date, path, SHA-256 hash |
| **Duplicate Detection** | SHA-256 hashing prevents importing the same file twice |
| **Smart File Organiser** | Rename and move imported files using 25+ naming tokens (course code, item type, semester, etc.) |

### Academic Tools
| Feature | Details |
|---------|---------|
| **GPA Calculator** | Enter grades manually or pull from tracked items; what-if simulation |
| **Weighted GPA** | Optional rule: Tests + Quizzes combined must exceed a threshold; shows both actual and weighted GPA |
| **Grade Weight Policy** | Per-course weight presets by item type (e.g., Exams 40%, Assignments 30%, Quizzes 15%, Projects 15%) |
| **Study Tracker** | Course-aware Pomodoro timer with focus/break phases, session history, per-course time stats |
| **Note Writer** | Distraction-free OmmWriter-inspired note editor with ambient sounds, backgrounds, typing sounds, auto-save, and backup history |
| **Academic Calendar** | Monthly calendar view showing all items with due dates |

### Import / Export
| Feature | Details |
|---------|---------|
| **ICS Export** | Export all deadlines as an `.ics` file importable into Apple Calendar, Google Calendar, Outlook |
| **ICS Import** | Parse `.ics` files from any calendar app and create academic items automatically |
| **CSV Export** | Export academic items to spreadsheet |
| **Local Backup** | Download a full JSON backup of all your data (courses, items, semesters, files) |
| **Cloud Backup** | Export data then open Google Drive / OneDrive / iCloud with one click for manual upload |

### Technical
| Feature | Details |
|---------|---------|
| **REST API** | 80+ endpoints; full Swagger UI at `/docs` |
| **API Key Auth** | Every API call requires `X-API-Key` header |
| **WebSocket** | Real-time update channel at `/ws` |
| **LMS Integration Stubs** | Blackboard, Canvas, Moodle, Google Classroom — ready for config |
| **Word Document Extraction** | Extract assignment metadata from `.docx` files |
| **File Watcher** | Monitor an inbox directory and auto-import new files |

---

## Quick Start

### Linux / macOS (Development)

```bash
git clone https://github.com/yourusername/scholarr.git
cd scholarr
pip install -e ".[dev]"
uvicorn scholarr.app:create_app --factory --host 0.0.0.0 --port 8787
# Open http://localhost:8787
```

### Docker

```bash
docker-compose up -d
# Open http://localhost:8787
```

### Linux (Production install)

```bash
sudo bash distribution/linux/install.sh
sudo systemctl start scholarr
journalctl -u scholarr -f
```

### macOS

```bash
bash distribution/macos/install.sh
launchctl load ~/Library/LaunchAgents/com.scholarr.agent.plist
```

### Windows

```powershell
PowerShell -ExecutionPolicy Bypass -File distribution\windows\install.ps1
```

---

## Configuration

All options can be set via environment variables or a `.env` file in the project root.

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHOLARR_API_KEY` | *(generated at startup)* | API authentication key — shown in startup logs |
| `SCHOLARR_DATABASE_URL` | `sqlite+aiosqlite:///./scholarr.db` | Database URL. SQLite for dev; `mysql+aiomysql://` or `postgresql+asyncpg://` for production |
| `SCHOLARR_HOST` | `0.0.0.0` | Bind address |
| `SCHOLARR_PORT` | `8787` | Port |
| `SCHOLARR_DEBUG` | `false` | Enable FastAPI debug mode and SQL query logging |
| `SCHOLARR_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `SCHOLARR_INBOX_PATH` | `~/Scholarr/Inbox` | Directory watched for incoming files |
| `SCHOLARR_SENTRY_DSN` | *(optional)* | Sentry error tracking DSN |

See `.env.example` for a complete template.

### Default data paths

| OS | Config | Data |
|----|--------|------|
| Linux | `~/.config/scholarr/` | `~/.local/share/scholarr/` |
| macOS | `~/.config/scholarr/` | `~/.local/share/scholarr/` |
| Windows | `%APPDATA%\Scholarr\` | `%LOCALAPPDATA%\Scholarr\` |

---

## Pages

| URL | Page |
|-----|------|
| `/` | Dashboard — stats, activity, upcoming deadlines, grade summary |
| `/courses` | Course list with search, semester filter, sort, pagination |
| `/courses/add` | Add course form |
| `/courses/{id}` | Course detail: files, items, study & activity, grade weight settings |
| `/academic-items` | All academic items with full filtering and CSV/ICS export |
| `/semesters` | Semester management |
| `/calendar` | Monthly calendar with ICS/CSV import and export |
| `/activity` | Full activity log with event type filtering |
| `/library` | File library with metadata panel, upload, rename, move |
| `/gpa` | GPA calculator with weighted mode |
| `/study-timer` | Course-aware Pomodoro study timer |
| `/notes` | Notes list with search, course filter, pinning |
| `/notes/{id}` | Distraction-free note editor with toolbar |
| `/settings` | App settings, backup/restore, cloud export |
| `/system` | System info and health |
| `/docs` | Interactive API documentation (Swagger UI) |

---

## Development

### Prerequisites

- Python 3.11+
- SQLite is used automatically for development — no database server needed
- MySQL 8.0+ or PostgreSQL for production

### Setup

```bash
pip install -e ".[dev]"

# Run with auto-reload
uvicorn scholarr.app:create_app --factory --port 8787 --reload
```

The app generates an API key on first start and prints it to the console. Set `SCHOLARR_API_KEY=your-key` in `.env` to use a fixed key.

### Testing

```bash
# Run all 281 tests (in-memory SQLite, no server needed)
pytest tests/ -q

# With coverage report
pytest tests/ --cov=scholarr --cov-report=html

# Only integration tests
pytest tests/integration/ -v
```

### Seed Data

Populate the database with sample data for testing:

```bash
SCHOLARR_API_KEY=test-key-12345 uvicorn scholarr.app:create_app --factory --port 8787 &
python seed_data.py
```

This creates 4 semesters, 12 courses, 35+ academic items with realistic grades and due dates, and 13 notes with course associations.

### Code quality

```bash
ruff check scholarr tests
mypy scholarr
```

---

## API

Full interactive documentation is available at `http://localhost:8787/docs` when the server is running.

All requests must include the header:
```
X-API-Key: <your-api-key>
```

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/semesters` | List semesters (includes `course_count`) |
| `POST` | `/api/v1/semesters` | Create semester (`year`/`term` auto-derived from name if omitted) |
| `PUT` | `/api/v1/semesters/{id}/activate` | Set active semester |
| `GET` | `/api/v1/courses` | List courses (includes `item_count`, `semester_name`, `grade_weights`) |
| `GET` | `/api/v1/courses/paged` | Paginated courses with `search`, `semester_id`, `monitored`, `sort_key`, `sort_dir` |
| `POST` | `/api/v1/courses` | Create course (`semester_id` optional — falls back to active semester) |
| `GET` | `/api/v1/academic-items` | List items with `search`, `type`, `status`, `course_id`, `due_after`, `due_before` |
| `GET` | `/api/v1/academic-items/upcoming` | Deadlines within `?days=N` (default 7); includes `course_code` |
| `GET` | `/api/v1/files` | List all managed files with `course_code`, `item_name` enrichment |
| `POST` | `/api/v1/files/{id}/rename` | Rename file on disk with history logging |
| `POST` | `/api/v1/files/{id}/move` | Move file to different academic item |
| `POST` | `/api/v1/import/manual/file` | Upload file linked to an academic item |
| `GET` | `/api/v1/history` | Activity log with `event_type`, `course_id` filters |
| `GET` | `/api/v1/tags` | List tags |
| `POST` | `/api/v1/integrations/calendar/generate-ics` | Generate `.ics` from academic items |
| `GET` | `/api/v1/system/status` | System health and runtime info |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+ (Docker uses 3.13), FastAPI, SQLAlchemy 2.0 (async), Pydantic V2 |
| **Frontend** | Jinja2 templates, Vanilla JS (`window.API` fetch helper), inline SVG icons |
| **Database** | SQLite + aiosqlite (dev) / MySQL 8 / PostgreSQL (prod) |
| **Auth** | API key (`X-API-Key` header), injected server-side into all templates |
| **Real-time** | WebSocket at `/ws` |
| **Infrastructure** | Docker, docker-compose, systemd, LaunchAgent, Windows Service |
| **Tests** | pytest-asyncio, 281 tests, in-memory SQLite |

---

## Troubleshooting

**Port 8787 already in use**
```
SCHOLARR_PORT=9000 uvicorn scholarr.app:create_app --factory --port 9000
```

**"No semester found" when creating a course**
Create a semester first at `/semesters`, then add courses.

**Database issues in development**
Delete `scholarr.db` in the project root to start fresh. The schema is created automatically on startup.

**Production database connection**
Set `SCHOLARR_DATABASE_URL` to a valid async URL:
- MySQL: `mysql+aiomysql://user:pass@host:3306/scholarr`
- PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/scholarr`

**Permission errors (Linux/macOS)**
```bash
sudo chown -R scholarr:scholarr /opt/scholarr
chmod +x distribution/linux/install.sh
```

---

## License

GPL-3.0 — see [LICENSE](LICENSE) for details.
