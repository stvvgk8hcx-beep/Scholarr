"""Import services for academic files and data."""

import asyncio
import csv
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import FileOperationError
from scholarr.core.import_sources.decision_engine import DecisionEngine, ImportAction
from scholarr.core.parser import FileNameParser, ItemType
from scholarr.db.models import AcademicItemStatusEnum, HistoryEventTypeEnum

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of a file import operation."""

    success: bool
    managed_file_id: int | None = None
    message: str = ""
    warnings: list[str] = field(default_factory=list)


class ImportService:
    """Service for importing academic files through a 6-step pipeline."""

    def __init__(self, session: AsyncSession):
        """Initialize import service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.parser = FileNameParser()
        self.decision_engine = DecisionEngine(session)

    async def import_file(self, file_path: str | Path, source_type: str = "Manual") -> ImportResult:
        """Import a file through the complete 6-step pipeline.

        Steps:
        1. Scan - validate file exists and get metadata
        2. Parse - extract metadata from filename
        3. Identify - fuzzy match course code
        4. Decide - check FileProfile rules and duplicates
        5. Organize - rename and move to library
        6. Record - create database entries and broadcast event

        Args:
            file_path: Path to the file to import.
            source_type: Type of import source (Manual, FileWatcher, etc).

        Returns:
            ImportResult: Result of the import operation.
        """
        file_path = Path(file_path)

        # Step 1: Scan
        try:
            scan_result = await self._step_scan(file_path)
            if not scan_result["success"]:
                return ImportResult(
                    success=False, message=f"Scan failed: {scan_result['message']}"
                )
        except Exception as e:
            logger.error(f"Error during scan step: {e}")
            return ImportResult(success=False, message=f"Scan failed: {e}")

        metadata = scan_result["metadata"]

        # Step 2: Parse
        try:
            parse_result = self._step_parse(file_path.name)
            logger.info(
                f"Parsed file {file_path.name}: course_code={parse_result.course_code}, "
                f"item_type={parse_result.item_type}, confidence={parse_result.confidence_score}"
            )
        except Exception as e:
            logger.error(f"Error during parse step: {e}")
            return ImportResult(success=False, message=f"Parse failed: {e}")

        # Step 3: Identify
        try:
            course_result = await self._step_identify(parse_result.course_code)
            if not course_result["success"]:
                return ImportResult(
                    success=False,
                    message=f"Could not identify course: {course_result['message']}",
                )
            course = course_result["course"]
        except Exception as e:
            logger.error(f"Error during identify step: {e}")
            return ImportResult(success=False, message=f"Identify failed: {e}")

        # Step 4: Decide
        try:
            decision = await self.decision_engine.evaluate(str(file_path), parse_result, course.id)

            if decision.action == ImportAction.REJECT:
                return ImportResult(success=False, message=f"Import rejected: {decision.reason}")

            if decision.action == ImportAction.SKIP:
                return ImportResult(
                    success=True,
                    managed_file_id=decision.existing_file_id,
                    message=f"File skipped: {decision.reason}",
                )

            if decision.action == ImportAction.UPGRADE:
                logger.info(
                    f"File will upgrade existing file {decision.existing_file_id}: "
                    f"{decision.reason}"
                )
        except Exception as e:
            logger.error(f"Error during decide step: {e}")
            return ImportResult(success=False, message=f"Decision failed: {e}")

        # Step 5 & 6: Organize and Record
        try:
            final_result = await self._step_organize_and_record(
                file_path, parse_result, course, metadata, source_type, decision
            )
            return final_result
        except Exception as e:
            logger.error(f"Error during organize/record steps: {e}")
            return ImportResult(success=False, message=f"Organization/recording failed: {e}")

    async def _step_scan(self, file_path: Path) -> dict:
        """Step 1: Scan file and validate it exists with metadata.

        Args:
            file_path: Path to file.

        Returns:
            dict: {success, message, metadata}
        """
        try:
            if not file_path.exists():
                return {"success": False, "message": f"File not found: {file_path}"}

            if not file_path.is_file():
                return {"success": False, "message": f"Path is not a file: {file_path}"}

            # Get file metadata
            stat = file_path.stat()
            file_size = stat.st_size
            extension = file_path.suffix.lstrip(".")

            # Calculate hash
            file_hash = await self._calculate_hash(file_path)

            metadata = {
                "size": file_size,
                "extension": extension,
                "hash": file_hash,
                "scanned_at": datetime.utcnow(),
            }

            logger.info(
                f"Scanned file {file_path.name}: size={file_size}, "
                f"ext={extension}, hash={file_hash[:8]}..."
            )
            return {"success": True, "metadata": metadata}
        except Exception as e:
            return {"success": False, "message": f"Scan error: {e}"}

    def _step_parse(self, filename: str) -> object:
        """Step 2: Parse filename to extract metadata.

        Args:
            filename: Filename to parse.

        Returns:
            ParseResult: Parsed metadata.
        """
        return self.parser.parse(filename)

    async def _step_identify(self, course_code: str | None) -> dict:
        """Step 3: Identify course using fuzzy matching.

        Args:
            course_code: Extracted course code.

        Returns:
            dict: {success, message, course}
        """
        from scholarr.db.models import Course

        if not course_code:
            return {"success": False, "message": "No course code extracted from filename"}

        # Try exact match first
        result = await self.session.execute(
            select(Course).where(Course.code == course_code)
        )
        course = result.scalar_one_or_none()

        if course:
            logger.info(f"Identified course: {course.code}")
            return {"success": True, "course": course}

        # Try case-insensitive match
        result = await self.session.execute(
            select(Course).where(Course.code.ilike(course_code))
        )
        course = result.scalar_one_or_none()

        if course:
            logger.info(f"Identified course (case-insensitive): {course.code}")
            return {"success": True, "course": course}

        # Try fuzzy match with Levenshtein distance
        course = await self._fuzzy_match_course(course_code)
        if course:
            logger.info(f"Identified course (fuzzy match): {course.code}")
            return {"success": True, "course": course}

        return {"success": False, "message": f"No matching course found for: {course_code}"}

    async def _step_organize_and_record(
        self, file_path: Path, parse_result, course, metadata: dict, source_type: str, decision
    ) -> ImportResult:
        """Steps 5 & 6: Organize file and record in database.

        Args:
            file_path: Path to file.
            parse_result: Parsed filename result.
            course: Course record.
            metadata: File metadata from scan.
            source_type: Import source type.
            decision: Decision engine result.

        Returns:
            ImportResult: Final import result.
        """
        from scholarr.db.models import ManagedFile

        try:
            # Find or create academic item
            academic_item = await self._find_or_create_academic_item(
                course, parse_result
            )

            # Organize file (rename and move)
            new_file_path = await self._organize_file(
                file_path, course, academic_item, metadata
            )

            # Record in database
            managed_file = ManagedFile(
                academic_item_id=academic_item.id,
                path=str(new_file_path),
                original_path=str(file_path),
                original_filename=file_path.name,
                size=metadata["size"],
                format=metadata["extension"],
                quality=self._determine_quality(metadata["extension"]),
                hash=metadata["hash"],
                version=1,
                date_imported=datetime.utcnow(),
            )

            self.session.add(managed_file)
            await self.session.commit()
            await self.session.refresh(managed_file)

            # Record history entry
            await self._record_history(
                course, academic_item, managed_file, "IMPORT", file_path, new_file_path
            )

            logger.info(f"Successfully imported file: {new_file_path}")
            return ImportResult(
                success=True,
                managed_file_id=managed_file.id,
                message=f"File imported successfully to {new_file_path}",
            )

        except Exception as e:
            logger.error(f"Error in organize/record: {e}")
            raise

    async def _find_or_create_academic_item(self, course, parse_result) -> object:
        """Find or create academic item for the import.

        Args:
            course: Course record.
            parse_result: Parsed filename result.

        Returns:
            AcademicItem: The academic item.
        """
        from scholarr.db.models import AcademicItem, AcademicItemTypeEnum

        # Try to find existing item
        item_type = parse_result.item_type or "Other"
        if isinstance(item_type, ItemType):
            item_type = item_type.value

        # Try to match by type and number
        if parse_result.item_number:
            result = await self.session.execute(
                select(AcademicItem).where(
                    (AcademicItem.course_id == course.id)
                    & (AcademicItem.type == AcademicItemTypeEnum(item_type))
                    & (AcademicItem.number == parse_result.item_number)
                )
            )
            academic_item = result.scalar_one_or_none()
            if academic_item:
                return academic_item

        # Create new item
        academic_item = AcademicItem(
            course_id=course.id,
            type=AcademicItemTypeEnum(item_type),
            name=parse_result.item_topic or f"{item_type}",
            number=parse_result.item_number,
            topic=parse_result.topic,
            status=AcademicItemStatusEnum.NOT_STARTED,
        )
        self.session.add(academic_item)
        await self.session.commit()
        await self.session.refresh(academic_item)

        logger.info(f"Created academic item: {academic_item.name} (ID: {academic_item.id})")
        return academic_item

    async def _organize_file(
        self, file_path: Path, course, academic_item, metadata: dict
    ) -> Path:
        """Organize file by moving it to proper location.

        Args:
            file_path: Current file path.
            course: Course record.
            academic_item: Academic item record.
            metadata: File metadata.

        Returns:
            Path: New file path.
        """
        # Determine target directory
        if course.root_folder_path:
            target_dir = Path(course.root_folder_path) / academic_item.name
        else:
            # Use default library location
            target_dir = Path.home() / "Scholarr" / "Library" / course.code / academic_item.name

        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Build new filename
        from scholarr.core.organizer import FileNameBuilder
        builder = FileNameBuilder()
        new_filename = builder.clean_filename(file_path.name)

        # Target path
        new_file_path = target_dir / new_filename

        # Handle duplicate filenames
        counter = 1
        while new_file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            new_filename = f"{stem}_{counter}{suffix}"
            new_file_path = target_dir / new_filename
            counter += 1

        # Copy file to new location
        try:
            with open(file_path, "rb") as src, open(new_file_path, "wb") as dst:
                dst.write(src.read())
            logger.info(f"Organized file: {file_path} -> {new_file_path}")
        except OSError as e:
            raise FileOperationError(f"Could not move file: {e}") from e

        return new_file_path

    async def _record_history(
        self, course, academic_item, managed_file, event_type: str, source_path, dest_path
    ):
        """Record history entry for the import.

        Args:
            course: Course record.
            academic_item: Academic item record.
            managed_file: Managed file record.
            event_type: Type of event.
            source_path: Source file path.
            dest_path: Destination file path.
        """
        from scholarr.db.models import HistoryEntry

        history = HistoryEntry(
            course_id=course.id,
            academic_item_id=academic_item.id,
            managed_file_id=managed_file.id,
            source_path=str(source_path),
            destination_path=str(dest_path),
            event_type=HistoryEventTypeEnum.IMPORT,
            date=datetime.utcnow(),
            data={
                "import_source": "Manual",
                "original_filename": managed_file.original_filename,
            },
        )
        self.session.add(history)
        await self.session.commit()

    async def _fuzzy_match_course(self, course_code: str):
        """Find course using fuzzy matching.

        Args:
            course_code: Course code to match.

        Returns:
            Course: Matching course or None.
        """
        from scholarr.db.models import Course

        result = await self.session.execute(select(Course))
        courses = result.scalars().all()

        # Simple Levenshtein distance matching
        best_match = None
        best_distance = float("inf")
        threshold = 2

        for course in courses:
            distance = self._levenshtein_distance(course_code.upper(), course.code.upper())
            if distance < best_distance and distance <= threshold:
                best_distance = distance
                best_match = course

        return best_match

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Args:
            s1: First string.
            s2: Second string.

        Returns:
            int: Levenshtein distance.
        """
        if len(s1) < len(s2):
            return ImportService._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    async def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file.

        Args:
            file_path: Path to file.

        Returns:
            str: Hex-encoded hash.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _determine_quality(self, extension: str) -> str:
        """Determine file quality based on extension.

        Args:
            extension: File extension.

        Returns:
            str: Quality level (High, Medium, Low).
        """
        extension = extension.lower()
        if extension in ("pdf", "docx"):
            return "High"
        elif extension in ("xlsx", "xls", "csv"):
            return "Medium"
        else:
            return "Low"


class FileWatcherProvider:
    """Provider for watching directories for new files."""

    def __init__(self, session: AsyncSession):
        """Initialize file watcher.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.import_service = ImportService(session)
        self.queue = asyncio.Queue()
        self.watched_paths = {}

    async def watch(self, path: str):
        """Start watching a directory for new files.

        Args:
            path: Directory path to watch.
        """
        try:
            from watchdog.observers import Observer

            path_obj = Path(path)
            if not path_obj.exists():
                logger.error(f"Watch path does not exist: {path}")
                return

            handler = FileWatcherEventHandler(self.queue)
            observer = Observer()
            observer.schedule(handler, str(path_obj), recursive=True)
            observer.start()

            self.watched_paths[path] = observer
            logger.info(f"Started watching directory: {path}")

            # Process queue in background
            asyncio.create_task(self._process_queue())
        except ImportError:
            logger.error("watchdog not installed. File watcher not available.")

    async def stop_watching(self, path: str):
        """Stop watching a directory.

        Args:
            path: Directory path to stop watching.
        """
        if path in self.watched_paths:
            observer = self.watched_paths[path]
            observer.stop()
            observer.join()
            del self.watched_paths[path]
            logger.info(f"Stopped watching directory: {path}")

    async def _process_queue(self):
        """Process queued files for import."""
        debounce_time = 2  # seconds
        pending = {}

        while True:
            try:
                file_path = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Debounce to handle partial writes
                if file_path in pending:
                    pending[file_path].cancel()

                async def import_after_delay(path):
                    await asyncio.sleep(debounce_time)
                    result = await self.import_service.import_file(path, "FileWatcher")
                    logger.info(
                        f"File watcher import: {path} - "
                        f"{'success' if result.success else 'failed'}"
                    )

                pending[file_path] = asyncio.create_task(import_after_delay(file_path))

            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing watched file: {e}")


try:
    from watchdog.events import FileSystemEventHandler as _BaseHandler
except ImportError:
    _BaseHandler = object  # type: ignore[assignment,misc]


class FileWatcherEventHandler(_BaseHandler):  # type: ignore[misc]
    """Event handler for file system events."""

    def __init__(self, queue: asyncio.Queue):
        """Initialize event handler.

        Args:
            queue: Queue to put file paths.
        """
        super().__init__()
        self.queue = queue

    def on_created(self, event):
        """Handle file creation event.

        Args:
            event: File system event.
        """
        if not event.is_directory:
            try:
                self.queue.put_nowait(event.src_path)
                logger.debug(f"Queued file for import: {event.src_path}")
            except Exception as e:
                logger.error(f"Error queuing file: {e}")


class CsvImportProvider:
    """Provider for bulk importing from CSV files."""

    def __init__(self, session: AsyncSession):
        """Initialize CSV import provider.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.import_service = ImportService(session)

    async def import_from_csv(self, csv_path: str | Path) -> list[ImportResult]:
        """Import academic items and files from CSV.

        Expected columns: course_code, item_type, item_number, topic, due_date, file_path

        Args:
            csv_path: Path to CSV file.

        Returns:
            list[ImportResult]: Results for each file imported.
        """
        results = []
        csv_path = Path(csv_path)

        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return [ImportResult(success=False, message=f"CSV file not found: {csv_path}")]

        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        result = await self._import_csv_row(row)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error importing CSV row {row_num}: {e}")
                        results.append(
                            ImportResult(
                                success=False,
                                message=f"Error in row {row_num}: {e}",
                            )
                        )
            logger.info(f"CSV import complete: {len(results)} rows processed")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return [ImportResult(success=False, message=f"CSV read error: {e}")]

        return results

    async def _import_csv_row(self, row: dict) -> ImportResult:
        """Import a single row from CSV.

        Args:
            row: Dictionary of row data.

        Returns:
            ImportResult: Result of import.
        """
        file_path = row.get("file_path", "").strip()
        if not file_path:
            return ImportResult(success=False, message="file_path not specified")

        return await self.import_service.import_file(file_path, "CsvImport")


class ManualEntryProvider:
    """Provider for manual import with explicit field specification."""

    def __init__(self, session: AsyncSession):
        """Initialize manual entry provider.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.import_service = ImportService(session)

    async def import_manual(
        self,
        file_path: str | Path,
        course_id: int,
        item_type: str,
        item_number: str | None = None,
        topic: str | None = None,
        due_date: datetime | None = None,
    ) -> ImportResult:
        """Import a file with manually specified metadata.

        Args:
            file_path: Path to the file.
            course_id: ID of the course.
            item_type: Type of academic item.
            item_number: Item number (e.g., "3" or "3.5").
            topic: Topic/description.
            due_date: Due date for the item.

        Returns:
            ImportResult: Result of the import.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return ImportResult(success=False, message=f"File not found: {file_path}")

        try:
            result = await self.import_service.import_file(str(file_path), "Manual")

            if result.success and result.managed_file_id:
                # Update the academic item with provided metadata
                from scholarr.core.managed_files import ManagedFileService

                managed_file_service = ManagedFileService(self.session)
                managed_file = await managed_file_service.get_by_id(result.managed_file_id)

                if topic:
                    managed_file.academic_item.topic = topic
                if item_number:
                    managed_file.academic_item.number = item_number
                if due_date:
                    managed_file.academic_item.due_date = due_date

                self.session.add(managed_file.academic_item)
                await self.session.commit()

            return result
        except Exception as e:
            logger.error(f"Error in manual import: {e}")
            return ImportResult(success=False, message=f"Manual import failed: {e}")
