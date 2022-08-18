import os

from dotenv import load_dotenv
from http import HTTPStatus
import telegram
import time
import requests

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class SendMessageException(Exception):
    """Ошибка отправки сообщения."""


class TokenException(Exception):
    """Ошибка наличия токена."""


class ResponseException(Exception):
    """Ошибка полученных данных по запросу."""


class APIErrorException(Exception):
    """Ошибка HTTP-статуса запроса к API."""


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        raise SendMessageException('Не удалось отправить сообщение!')


def get_api_answer(current_timestamp):
    """Получает данные от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        text_error = (f'Запрос к API вернул статус отличный от 200: '
                      f'{response.status_code}')
        raise APIErrorException(text_error)
    else:
        return response.json()


def check_response(response):
    """Проверяет результат запроса на соответствие ожиданиям."""
    if 'homeworks' not in response:
        text_error = 'В ответе на запрос отсутствует ключ "homeworks"'
        raise ResponseException(text_error)
    status_homeworks = response['homeworks'][0]['status']
    if status_homeworks not in HOMEWORK_STATUSES:
        text_error = (f'Полученный статус {status_homeworks} '
                      f'отсутствует в списке ожидаемых статусов!')
        raise ResponseException(text_error)
    return response['homeworks'][0]


def parse_status(homework):
    """Выдает текст с результатами ревью."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие всех необходимых переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    tokens_status = True
    text_error = 'Прогамма остановлена! Не найдена необходимая переменная:'
    for token in tokens:
        if token is None:
            tokens_status = False
            raise TokenException(f'{text_error} {token}')
        else:
            tokens_status = True
    return tokens_status


def main():
    """Основная логика работы бота."""
    tokens_are_available = check_tokens()
    if tokens_are_available is False:
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    MONTH = 2629743
    current_timestamp = int(time.time()) - MONTH
    default_status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            print(response)
            homework = check_response(response)
            print(homework)
            if homework and default_status != homework['status']:
                message = parse_status(homework)
                send_message(bot, message)
                default_status = homework['status']
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
