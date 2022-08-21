import json
import logging
import os
import sys
import time
from http import HTTPStatus

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (APIErrorException,
                        APIJsonError,
                        HomeworksKeyError,
                        ResponseError,
                        SendMessageException,)


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


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        text_error = f'Не удалось отправить сообщение: {message}'
        raise SendMessageException(text_error)
    else:
        info = f'В телеграм отправлено сообщение: {message}'
        logging.info(info)


def get_api_answer(current_timestamp):
    """Получает данные от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            text_error = (f'API недоступен! Статус-код: '
                          f'{response.status_code}')
            raise APIErrorException(text_error)
        info = 'Запрос к API выполнен успешно!'
        logging.info(info)
        return response.json()

    except requests.exceptions.RequestException as error:
        text_error = f'Ошибка выполения запроса к API: {error}'
        raise ResponseError(text_error)
    except json.JSONDecodeError as error:
        text_error = f'Ошибка в данных ответа API(ValueError): {error}'
        raise APIJsonError(text_error)


def check_response(response):
    """Проверяет результат запроса на соответствие ожиданиям."""
    if response['homeworks'] == []:
        text_error = 'От API получен пустой список проверяемых работ.'
        raise TypeError(text_error)
    if 'homeworks' not in response:
        text_error = 'В ответе на запрос отсутствует ключ "homeworks"'
        raise ValueError(text_error)
    homework = response['homeworks']
    if homework[0] is None:
        text_error = 'Нет списка проверяемых работ.'
        raise ValueError(text_error)
    if not isinstance(homework[0], dict):
        text_error = f'Ошибка типа данных! {homework} не словарь!'
        raise TypeError(text_error)
    else:
        return homework


def parse_status(homework):
    """Выдает текст с результатами ревью."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        homework_name = 'нет названия'
        text_error = 'В ответе от API отсутствует ключ "homework_name"'
        logging.debug(text_error)
    homework_status = homework.get('status')
    if homework_status is None:
        text_error = 'В ответе от API отсутствует ключ "status"'
        raise HomeworksKeyError(text_error)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие всех необходимых переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = (
            'Ошибка: отсутствует(ют) обязательная(ые) '
            'переменная(ые) окружения!'
        )
        logging.critical(message)
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    start_message = 'Бот начал свою работу!'
    send_message(bot, start_message)
    current_timestamp = int(time.time())
    default_status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if default_status != homework[0]['status']:
                message = parse_status(homework[0])
                send_message(bot, message)
                default_status = homework[0]['status']
            else:
                info = f'Статус не изменился. Ждем еще {RETRY_TIME} сек.'
                logging.debug(info)

        except Exception as error:
            text_error = f'Сбой в работе программы: {error}'
            logging.critical(message)
            send_message(bot, text_error)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        encoding='utf-8',
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)
    main()
