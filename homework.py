import os

from dotenv import load_dotenv
from http import HTTPStatus
import logging
import requests
import telegram
import time

from exceptions import (APIErrorException,
                        SendMessageException,
                        )

bot = ''

logging.basicConfig(
    encoding='utf-8',
    level=logging.DEBUG,
    filename='program.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

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
        info = f'В телеграм отправлено сообщение: {message}'
        logging.info(info)
    except Exception:
        text_error = f'Не удалось отправить сообщение: {message}'
        logging.exception(text_error)
        raise SendMessageException(text_error)


def get_api_answer(current_timestamp):
    """Получает данные от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        text_error = (f'API недоступен! Статус-код: '
                      f'{response.status_code}')
        logging.error(text_error)
        send_message(bot, text_error)
        raise APIErrorException(text_error)
    else:
        info = 'Запрос к API выполнен успешно!'
        logging.info(info)
        return response.json()


def check_response(response):
    """Проверяет результат запроса на соответствие ожиданиям."""
    if response['homeworks'] == []:
        text_error = 'Получен список вместо словаря.'
        logging.error(text_error)
        send_message(bot, text_error)
        raise TypeError(text_error)
    if 'homeworks' not in response:
        text_error = 'В ответе на запрос отсутствует ключ "homeworks"'
        logging.error(text_error)
        send_message(bot, text_error)
        raise ValueError(text_error)
    homework = response['homeworks']
    if not isinstance(homework[0], dict):
        text_error = f'Ошибка типа данных! {homework} не словарь!'
        logging.error(text_error)
        send_message(bot, text_error)
        raise TypeError(text_error)
    else:
        return homework


def parse_status(homework):
    """Выдает текст с результатами ревью."""
    try:
        homework_name = homework.get('homework_name')
    except KeyError:
        text_error = 'В ответе от API отсутствует ключ "homework_name"'
        logger.error(text_error)
        send_message(bot, text_error)
    try:
        homework_status = homework.get('status')
    except KeyError:
        text_error = 'В ответе от API отсутствует ключ "status"'
        logger.error(text_error)
        send_message(bot, text_error)
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
            message = f'{text_error} {token}'
            logging.critical(message)
        else:
            tokens_status = True
    return tokens_status


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        exit()
    MONTH = 2629743
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - MONTH
    default_status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework[0] and default_status != homework[0]['status']:
                message = parse_status(homework[0])
                send_message(bot, message)
                default_status = homework[0]['status']
            else:
                info = f'Статус не изменился. Ждем еще {RETRY_TIME} сек.'
                logging.debug(info)
            time.sleep(RETRY_TIME)

        except Exception as error:
            text_error = f'Сбой в работе программы: {error}'
            logging.critical(message)
            send_message(bot, text_error)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
