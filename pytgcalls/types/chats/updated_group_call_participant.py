from ..chats import GroupCallParticipant
from ..update import Update


class UpdatedGroupCallParticipant(Update):
    def __init__(
        self,
        chat_id: int,
        participant: GroupCallParticipant,
    ):
        super().__init__(chat_id)
        self.participant = participant
