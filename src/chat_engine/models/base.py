"""Module for representing database entities and models."""

from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase, Mapped, RelationshipProperty, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )

    @classmethod
    def from_dict(cls, data: dict):
        """Create an instance of the model from a dictionary."""
        # Separate relationship data from plain column data
        relationship_data = {}
        column_data = {}

        # Get all defined relationships for this class
        mapper = cls.__mapper__

        for key, value in data.items():
            if key in mapper.relationships:
                rel_property: RelationshipProperty = mapper.relationships[key]
                target_class = rel_property.mapper.class_

                # Convert dict(s) to entity object(s)
                if isinstance(value, list):
                    relationship_data[key] = [target_class.from_dict(i) for i in value]
                elif isinstance(value, dict):
                    relationship_data[key] = target_class.from_dict(value)
            else:
                column_data[key] = value

        return cls(**column_data, **relationship_data)
