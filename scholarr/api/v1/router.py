"""Main v1 API router that includes all endpoint routers."""

from fastapi import APIRouter

from scholarr.api.v1.endpoints import (
    courses,
    semesters,
    academic_items,
    managed_files,
    file_profiles,
    root_folders,
    tags,
    naming,
    commands,
    queue,
    history,
    health,
    log,
    calendar,
    manual_import,
    file_import,
    file_system,
    custom_formats,
    notifications,
    backup,
    system,
    config,
    integrations,
    mass_editor,
)

router = APIRouter()

# Include all endpoint routers
router.include_router(courses.router, prefix="/courses", tags=["Courses"])
router.include_router(semesters.router, prefix="/semesters", tags=["Semesters"])
router.include_router(academic_items.router, prefix="/academic-items", tags=["Academic Items"])
router.include_router(managed_files.router, prefix="/files", tags=["Files"])
router.include_router(file_profiles.router, prefix="/file-profiles", tags=["File Profiles"])
router.include_router(root_folders.router, prefix="/root-folders", tags=["Root Folders"])
router.include_router(tags.router, prefix="/tags", tags=["Tags"])
router.include_router(naming.router, prefix="/naming", tags=["Naming"])
router.include_router(commands.router, prefix="/commands", tags=["Commands"])
router.include_router(queue.router, prefix="/queue", tags=["Queue"])
router.include_router(history.router, prefix="/history", tags=["History"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(log.router, prefix="/logs", tags=["Logs"])
router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
router.include_router(manual_import.router, prefix="/import", tags=["Import"])
router.include_router(file_import.router, prefix="/import/auto", tags=["Import"])
router.include_router(file_system.router, prefix="/file-system", tags=["File System"])
router.include_router(custom_formats.router, prefix="/custom-formats", tags=["Custom Formats"])
router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
router.include_router(backup.router, prefix="/backup", tags=["Backup"])
router.include_router(system.router, prefix="/system", tags=["System"])
router.include_router(config.router, prefix="/config", tags=["Configuration"])
router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
router.include_router(mass_editor.router, prefix="/editor", tags=["Mass Editor"])
