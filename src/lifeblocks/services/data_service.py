import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, Enum, DateTime, inspect
from sqlalchemy.orm import Session
from sqlalchemy.schema import DDL
from lifeblocks.models import Block, TimeBlock, Settings
from lifeblocks.models.timeblock import TimeBlockState, PickReason

class DataService:
    CURRENT_VERSION = "1.13"

    def __init__(self, session: Session):
        self.session = session
        self.engine = session.get_bind()

    def ensure_schema_current(self):
        """Ensures all database schemas are current."""
        # Check if we're already at current version
        settings = self.session.query(Settings).filter(Settings.key == "schema_version").first()
        if settings and settings.value == self.CURRENT_VERSION:
            return

        inspector = inspect(self.engine)
        
        # Check TimeBlock schema
        timeblock_columns = {col['name']: col for col in inspector.get_columns(TimeBlock.__tablename__)}
        
        # Check Block schema
        block_columns = {col['name']: col for col in inspector.get_columns(Block.__tablename__)}
        
        # Close any existing transactions
        self.session.commit()
        
        # Execute schema updates in a separate connection
        with self.engine.begin() as connection:
            if 'state' not in timeblock_columns:
                # Add state column
                connection.execute(DDL(
                    f"ALTER TABLE {TimeBlock.__tablename__} "
                    f"ADD COLUMN state VARCHAR(20) DEFAULT '{TimeBlockState.COMPLETED.value}'"
                ))

            if 'pick_reason' not in timeblock_columns:
                # Add pick_reason column
                connection.execute(DDL(
                    f"ALTER TABLE {TimeBlock.__tablename__} "
                    "ADD COLUMN pick_reason VARCHAR(20) DEFAULT 'normal'"
                ))

            if 'pause_start' not in timeblock_columns:
                # Add pause_start column
                connection.execute(DDL(
                    f"ALTER TABLE {TimeBlock.__tablename__} "
                    "ADD COLUMN pause_start TIMESTAMP NULL"
                ))

            if 'forced' not in timeblock_columns:
                # Add forced column
                connection.execute(DDL(
                    f"ALTER TABLE {TimeBlock.__tablename__} "
                    "ADD COLUMN forced BOOLEAN DEFAULT FALSE"
                ))

            if 'delay_hours' not in timeblock_columns:
                # Add delay_hours column
                connection.execute(DDL(
                    f"ALTER TABLE {TimeBlock.__tablename__} "
                    "ADD COLUMN delay_hours INTEGER NULL"
                ))

            if 'created_at' not in block_columns:
                # Add created_at column (SQLite doesn't support adding NOT NULL columns with defaults)
                connection.execute(DDL(
                    f"ALTER TABLE {Block.__tablename__} "
                    "ADD COLUMN created_at TIMESTAMP"
                ))
                # Update all existing rows with current timestamp
                connection.execute(DDL(
                    f"UPDATE {Block.__tablename__} "
                    "SET created_at = CURRENT_TIMESTAMP"
                ))

        # Now update data in a new transaction
        if 'state' not in timeblock_columns:
            self.session.query(TimeBlock).update(
                {"state": TimeBlockState.COMPLETED},
                synchronize_session=False
            )

        if 'pick_reason' not in timeblock_columns:
            self.session.query(TimeBlock).update(
                {"pick_reason": PickReason.NORMAL},
                synchronize_session=False
            )
        
        # Update schema version
        if settings:
            settings.value = self.CURRENT_VERSION
        else:
            self.session.add(Settings(key="schema_version", value=self.CURRENT_VERSION))
        
        self.session.commit()

    def export_data(self) -> Dict[str, Any]:
        """Export database to a dictionary."""
        blocks = self.session.query(Block).all()
        timeblocks = self.session.query(TimeBlock).all()
        settings = self.session.query(Settings).all()

        return {
            "version": self.CURRENT_VERSION,
            "blocks": [
                {
                    "id": block.id,
                    "name": block.name,
                    "weight": block.weight,
                    "parent_id": block.parent_id,
                    "max_interval_hours": block.max_interval_hours,
                    "length_multiplier": block.length_multiplier,
                    "min_duration_minutes": block.min_duration_minutes,
                    "last_picked": block.last_picked.isoformat()
                    if block.last_picked
                    else None,
                }
                for block in blocks
            ],
            "timeblocks": [
                {
                    "id": tb.id,
                    "block_id": tb.block_id,
                    "start_time": tb.start_time.isoformat(),
                    "duration_minutes": tb.duration_minutes,
                    "resistance_level": tb.resistance_level,
                    "satisfaction_level": tb.satisfaction_level,
                    "pause_duration_minutes": tb.pause_duration_minutes,
                    "notes": tb.notes,
                    "deleted": tb.deleted,
                    "deleted_at": tb.deleted_at.isoformat() if tb.deleted_at else None,
                    "state": tb.state.value if tb.state else TimeBlockState.COMPLETED.value,
                    "pause_start": tb.pause_start.isoformat() if tb.pause_start else None,
                    "forced": tb.forced,
                    "delay_hours": tb.delay_hours,
                }
                for tb in timeblocks
            ],
            "settings": [
                {"key": setting.key, "value": setting.value} for setting in settings
            ],
        }

    def import_data(self, data: Dict[str, Any]) -> List[str]:
        """Import data into the database with version checking and migration support."""
        messages = []

        # Version check
        version = data.get("version", "1.0")  # Default to 1.0 for old exports
        if version != self.CURRENT_VERSION:
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
                    length_multiplier=block_data.get("length_multiplier", 1.0),
                    min_duration_minutes=block_data.get("min_duration_minutes"),
                )
                block.id = block_data["id"]  # Preserve original IDs
                if block_data.get("last_picked"):
                    block.last_picked = datetime.fromisoformat(block_data["last_picked"])
                self.session.add(block)

            # Import timeblocks
            for timeblock_data in data["timeblocks"]:
                timeblock = TimeBlock(
                    block_id=timeblock_data["block_id"],
                    start_time=datetime.fromisoformat(timeblock_data["start_time"]),
                    duration_minutes=timeblock_data["duration_minutes"],
                    resistance_level=timeblock_data.get("resistance_level"),
                    satisfaction_level=timeblock_data.get("satisfaction_level"),
                    pause_duration_minutes=timeblock_data.get("pause_duration_minutes", 0.0),
                    notes=timeblock_data.get("notes"),
                    state=TimeBlockState(timeblock_data.get("state", "completed")),
                    pause_start=datetime.fromisoformat(timeblock_data["pause_start"])
                        if timeblock_data.get("pause_start")
                        else None,
                    forced=timeblock_data.get("forced", False),
                    delay_hours=timeblock_data.get("delay_hours"),
                )
                timeblock.id = timeblock_data["id"]  # Preserve original IDs
                timeblock.deleted = timeblock_data.get("deleted", False)
                if timeblock_data.get("deleted_at"):
                    timeblock.deleted_at = datetime.fromisoformat(
                        timeblock_data["deleted_at"]
                    )
                self.session.add(timeblock)

            # Import settings
            for setting_data in data["settings"]:
                setting = Settings(key=setting_data["key"], value=setting_data["value"])
                self.session.add(setting)

            self.session.commit()
            messages.append("Import completed successfully")

        except Exception as e:
            self.session.rollback()
            messages.append(f"Error during import: {str(e)}")

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
