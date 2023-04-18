from enum import Enum, auto


class KartOperation(Enum):
    """
    Kart operations
    """

    Unknown = auto()
    Clone = auto()

    def to_present_tense_string(self) -> str:
        """
        Returns a present tense string representing the operation
        """
        return {
            KartOperation.Unknown: 'unknown',
            KartOperation.Clone: 'Cloning'
        }[self]

    def to_past_tense_string(self) -> str:
        """
        Returns a past tense string representing the operation
        """
        return {
            KartOperation.Unknown: 'unknown',
            KartOperation.Clone: 'Cloned'
        }[self]
