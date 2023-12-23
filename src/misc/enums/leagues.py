from enum import IntEnum, auto


class BandLeague(IntEnum):
    CROOKS = auto()  # Жулики
    GAMBLERS = auto()  # Картёжники
    CARD_MASTERS = auto()  # Мастера карт
    BUSINESSMEN = auto()  # Бизнесмены
    INDUSTRIALISTS = auto()  # Промышленники
    MAGNATES = auto()  # Магнаты
    MONOPOLISTS = auto()  # Монополисты

    def get_full_name(self) -> str:
        match self:
            case self.CROOKS:
                return 'Жулики'
            case self.GAMBLERS:
                return 'Картёжники'
            case self.CARD_MASTERS:
                return 'Мастера карт'
            case self.BUSINESSMEN:
                return 'Промышленники'
            case self.MAGNATES:
                return 'Магнаты'
            case self.MONOPOLISTS:
                return 'Монополисты'
