"""File quality profiles service for Scholarr."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class FileProfileService:
    """Service for managing file quality profiles."""

    def __init__(self, session: AsyncSession):
        """Initialize file profile service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self) -> list:
        """Get all file quality profiles.

        Returns:
            list: List of file profile records.
        """
        from scholarr.db.models import FileProfile

        result = await self.session.execute(select(FileProfile))
        return list(result.scalars().all())

    async def get_by_id(self, profile_id: int):
        """Get file profile by ID.

        Args:
            profile_id: Profile ID.

        Returns:
            FileProfile: The file profile record.

        Raises:
            NotFoundError: If profile not found.
        """
        from scholarr.db.models import FileProfile

        result = await self.session.execute(
            select(FileProfile).where(FileProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise NotFoundError(f"File profile {profile_id} not found")

        return profile

    async def create(self, data: dict):
        """Create a new file quality profile.

        Args:
            data: Dictionary containing profile data.

        Returns:
            FileProfile: The created file profile.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import FileProfile

        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        profile = FileProfile(**data)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def update(self, profile_id: int, data: dict):
        """Update an existing file quality profile.

        Args:
            profile_id: Profile ID.
            data: Dictionary of fields to update.

        Returns:
            FileProfile: The updated file profile.

        Raises:
            NotFoundError: If profile not found.
        """
        profile = await self.get_by_id(profile_id)

        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def delete(self, profile_id: int):
        """Delete a file quality profile.

        Args:
            profile_id: Profile ID.

        Raises:
            NotFoundError: If profile not found.
        """
        profile = await self.get_by_id(profile_id)
        await self.session.delete(profile)
        await self.session.commit()
