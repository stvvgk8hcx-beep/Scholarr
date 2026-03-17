# Scholarr

**Self-hosted academic file management**

A personal project to manage academic files, notes, and resources without relying on cloud services. Organize documents across courses and semesters, search full-text, calculate GPA, and track deadlines—all running locally on your machine.

## Features

- **Smart File Organization**: Automatically organize files using 25+ naming tokens for flexible folder structures
- **Multi-Course Management**: Handle multiple courses, semesters, and academic items
- **Full-Text Search**: Search across documents and metadata instantly
- **File Deduplication**: Automatic duplicate detection using SHA256 hashing
- **GPA Calculator**: Track grades and simulate what-if scenarios
- **Calendar Integration**: Visualize important dates and deadlines
- **REST API**: Full API with 80+ endpoints for programmatic access
- **Real-time Updates**: WebSocket support for live client synchronization
- **Dark Theme**: Sonarr/Radarr-inspired dark UI
- **Multiple Databases**: SQLite for development, MySQL or PostgreSQL for production
- **Cross-Platform**: Linux, Windows, and macOS support
- **Docker Ready**: Complete Docker and docker-compose setup
- **LMS Integration Stubs**: Blackboard, Canvas, Moodle, Google Classroom

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/yourusername/scholarr.git
cd scholarr
docker-compose up -d
# Access at http://localhost:8787
```

### Linux

```bash
sudo bash distribution/linux/install.sh
sudo systemctl start scholarr
journalctl -u scholarr -f  # View logs
```

### macOS

```bash
bash distribution/macos/install.sh
launchctl load ~/Library/LaunchAgents/com.scholarr.agent.plist
# Access at http://localhost:8787
```

### Windows

```powershell
PowerShell -ExecutionPolicy Bypass -File distribution\windows\install.ps1
# Follow the on-screen instructions
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHOLARR_DEBUG` | `false` | Enable debug mode |
| `SCHOLARR_HOST` | `0.0.0.0` | Server host |
| `SCHOLARR_PORT` | `8787` | Server port |
| `SCHOLARR_DATABASE_URL` | `sqlite+aiosqlite:///./scholarr.db` | Database connection string (SQLite for dev, MySQL/PostgreSQL for production) |
| `SCHOLARR_API_KEY` | (generated) | API authentication key |
| `SCHOLARR_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `SCHOLARR_SENTRY_DSN` | (optional) | Sentry error tracking URL |
| `SCHOLARR_INBOX_PATH` | (auto) | Directory to monitor for new files |

See `.env.example` for a complete template.

### Default Paths

- **Linux/macOS Config**: `~/.config/scholarr/`
- **Linux/macOS Data**: `~/.local/share/scholarr/`
- **Windows Config**: `%APPDATA%\Scholarr\`
- **Windows Data**: `%LOCALAPPDATA%\Scholarr\`

## Development

### Prerequisites

- Python 3.11+
- No external database needed for development (SQLite is used automatically)
- MySQL 8.0+ or PostgreSQL for production

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run the app (SQLite database created automatically)
uvicorn scholarr.app:app --host 0.0.0.0 --port 8787 --reload

# Or with Docker (uses MySQL)
docker-compose -f docker-compose.dev.yml up -d
```

### Testing & Quality

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=scholarr --cov-report=html

# Code quality
ruff check scholarr tests
mypy scholarr
```

## API Documentation

When running, check out the interactive API documentation:
- **Swagger UI**: `http://localhost:8787/docs`
- **ReDoc**: `http://localhost:8787/redoc`

## Tech Stack

**Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic V2
**Frontend**: Jinja2 templates, HTMX (no JavaScript frameworks)
**Database**: SQLite + aiosqlite (development), MySQL 8.0 / PostgreSQL (production)
**Infrastructure**: Docker, docker-compose, systemd/LaunchAgent/Windows Service
**Monitoring**: Sentry error tracking, structured logging
**Tests**: 281 tests (pytest-asyncio, in-memory SQLite)

## Contributing

Found a bug or want to add a feature? PRs welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write tests and ensure code quality (`ruff check`, `mypy`, `pytest`)
4. Commit and push: `git commit -m 'Add your feature' && git push origin feature/your-feature`
5. Open a Pull Request

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

**Port 8787 already in use?**
Set `SCHOLARR_PORT=9000` in your `.env` file or environment.

**Database connection issues?**
In development, SQLite is used automatically — no setup needed. For production, verify `SCHOLARR_DATABASE_URL` is set correctly (e.g. `mysql+aiomysql://user:pass@host/db`) and the database server is running.

**Permission errors on Linux/macOS?**
```bash
sudo chown -R scholarr:scholarr /opt/scholarr
chmod +x distribution/linux/install.sh
```
