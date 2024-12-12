import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from lifeblocks.models import Block, TimeBlock, Settings


class DataService:
    CURRENT_VERSION = "1.0"

    def __init__(self, session: Session):
        self.session = session

    def export_data(self) -> Dict[str, Any]:
        """Export all data from the database with version information."""
        blocks = self.session.query(Block).all()
        timeblocks = self.session.query(TimeBlock).all()
        settings = self.session.query(Settings).all()

        data = {
            "version": self.CURRENT_VERSION,
            "export_date": datetime.now().isoformat(),
            "blocks": [
                {
                    "id": p.id,
                    "name": p.name,
                    "weight": p.weight,
                    "parent_id": p.parent_id,
                    "last_picked": p.last_picked.isoformat() if p.last_picked else None,
                    "max_interval_minutes": p.max_interval_minutes,
                }
                for p in blocks
            ],
            "timeblocks": [
                {
                    "id": t.id,
                    "block_id": t.block_id,
                    "start_time": t.start_time.isoformat(),
                    "duration_minutes": t.duration_minutes,
                    "resistance_level": t.resistance_level,
                    "satisfaction_level": t.satisfaction_level,
                    "pause_duration_minutes": t.pause_duration_minutes,
                    "notes": t.notes,
                    "deleted": t.deleted,
                    "deleted_at": t.deleted_at.isoformat() if t.deleted_at else None,
                }
                for t in timeblocks
            ],
            "settings": [{"key": s.key, "value": s.value} for s in settings],
        }
        return data

    def import_data(self, data: Dict[str, Any]) -> List[str]:
        """Import data into the database with version checking and migration support.
        Returns a list of messages about the import process."""
        messages = []

        # Version check
        version = data.get("version")
        if version and version != self.CURRENT_VERSION:
            messages.append(
                f"Warning: Importing data from version {version} into version {self.CURRENT_VERSION}"
            )
            data = self._migrate_data(data, version)

        try:
            # Clear existing data
            self.session.query(TimeBlock).delete()
            self.session.query(Block).delete()
            self.session.query(Settings).delete()

            # Import blocks first (they're referenced by timeblocks)
            for block_data in data["blocks"]:
                block = Block(
                    name=block_data["name"],
                    weight=block_data["weight"],
                    parent_id=block_data["parent_id"],
                    max_interval_hours=block_data.get("max_interval_hours"),
                )
                block.id = block_data["id"]  # Preserve original IDs
                if block_data["last_picked"]:
                    block.last_picked = datetime.fromisoformat(
                        block_data["last_picked"]
                    )
                self.session.add(block)

            # Import timeblocks
            for timeblock_data in data["timeblocks"]:
                timeblock = TimeBlock(
                    block_id=timeblock_data["block_id"],
                    start_time=datetime.fromisoformat(timeblock_data["start_time"]),
                    duration_minutes=timeblock_data["duration_minutes"],
                    resistance_level=timeblock_data["resistance_level"],
                    satisfaction_level=timeblock_data["satisfaction_level"],
                    pause_duration_minutes=timeblock_data["pause_duration_minutes"],
                    notes=timeblock_data["notes"],
                )
                timeblock.id = timeblock_data["id"]  # Preserve original IDs
                timeblock.deleted = timeblock_data["deleted"]
                if timeblock_data["deleted_at"]:
                    timeblock.deleted_at = datetime.fromisoformat(
                        timeblock_data["deleted_at"]
                    )
                self.session.add(timeblock)

            # Import settings
            for setting_data in data["settings"]:
                setting = Settings(key=setting_data["key"], value=setting_data["value"])
                self.session.add(setting)

            self.session.commit()
            messages.append("Data import completed successfully")

        except Exception as e:
            self.session.rollback()
            messages.append(f"Error during import: {str(e)}")
            raise

        return messages

    def _migrate_data(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Handle data migration between versions.
        This method should be expanded as new versions are created."""
        # Currently we're at version 1.0, so no migrations are needed yet
        # Future migrations would be implemented here
        return data

    def export_to_file(self, filepath: str) -> None:
        """Export database to a JSON file."""
        data = self.export_data()
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def import_from_file(self, filepath: str) -> List[str]:
        """Import database from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return self.import_data(data)
