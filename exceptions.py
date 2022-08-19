class SendMessageException(Exception):
    """Ошибка отправки сообщения."""


class APIErrorException(Exception):
    """Ошибка HTTP-статуса запроса к API."""
