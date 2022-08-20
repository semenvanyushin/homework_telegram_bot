class SendMessageException(Exception):
    """Ошибка отправки сообщения."""


class APIErrorException(Exception):
    """Ошибка HTTP-статуса запроса к API."""


class APIJsonError(Exception):
    """Ошибка в данных ответа API."""


class HomeworksKeyError(Exception):
    """Ошибка наличия необходимых ключей в словаре."""


class ResponseError(Exception):
    """Ошибка выполнения запроса к API."""
