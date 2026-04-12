from enum import Enum
from chat_engine.models.enums import PreferenceType

class Avatar(Enum):
    """Enum representing the avatars"""

    AI = "🤖"  # ":robot:"
    ASSISTANT = "🧙‍♂️"  # ":wizard:"
    SYSTEM = "⚙"  # ":gear:"
    USER = "👤"  # ":bust_in_silhouette:"
    ADMIN = "👨‍⚖️"  # ":man_judge:"

    @staticmethod
    def parse(string: str):
        """Parse the string representation of the enum into an enum."""
        for avatar in Avatar:
            if avatar.name == string.upper():
                return avatar
        return None

parking_preferences = [preference.value for preference in PreferenceType]
