import json
import logging
import os
import sys
import time
from http import HTTPStatus

from dotenv import load_dotenv
import requests
import telegram


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, 'logging_bot.log')


def check_tokens() -> list[str]:
    """
    Проверяем доступность переменных окружения.
    И возвращаем список отсутствующих.
    """
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing_tokens = []
    for token_name, token_value in tokens.items():
        if not token_value:
            missing_tokens.append(token_name)
    if missing_tokens:
        missing_tokens_str = ', '.join(missing_tokens)
        return (f'Программа не будет работать. '
                f'Отсутствуют токены: {missing_tokens_str}')
    return ''


def send_message(bot: telegram.Bot, message: str) -> bool:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message,)
    except telegram.TelegramError as error:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {error}")
    else:
        logging.debug('Статус отправлен в telegram')


def get_api_answer(timestamp: int) -> dict:
    """Отправляет запрос к API-сервису и возвращает ответ."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(f'Код ответа: {response.status_code}')
        return response.json()
    except requests.RequestException as error:
        raise RuntimeError(f'Произошла ошибка при запросе к API: {error}')
    except json.JSONDecodeError as decode_error:
        raise RuntimeError(f'Ошибка при парсинге JSON данных: {decode_error}')


def check_response(response: dict) -> list:
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API должен быть в виде словаря')
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError('Отсутствует ключ "homeworks" в ответе API')
    if not isinstance(homeworks, list):
        raise TypeError('Значение ключа "homeworks" должно быть '
                        'представлено в виде списка')
    current_date = response.get('current_date')
    if current_date is None:
        logging.error('Отсутствует ключ "current_date" в ответе API')
    if not isinstance(current_date, int):
        raise TypeError('Значение ключа "current_date" должно быть '
                        'представлено в виде числа')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает статус, возвращает в Telegram строку статуса."""
    if not isinstance(homework, dict):
        raise TypeError('Полученный аргумент должен быть словарем.')
    status = homework.get('status')
    if 'status' not in homework:
        message = 'Нет ключа "status" в словаре домашней работы.'
        raise KeyError(message)
    verdict = HOMEWORK_VERDICTS.get(status)
    if verdict is None:
        message = f'Статус {status} не найден в HOMEWORK_VERDICTS.'
        raise ValueError(message)
    name = homework.get('homework_name')
    if 'homework_name' not in homework:
        message = 'Нет ключа "homework_name" в словаре домашней работы.'
        raise KeyError(message)
    return f'Изменился статус проверки работы "{name}". {verdict}'


def main():
    """Основная логика работы бота."""
    missing_tokens_message = check_tokens()
    if missing_tokens_message:
        logging.critical(missing_tokens_message)
        sys.exit(missing_tokens_message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 2592000
    last_message = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug("Домашних работ нет.")
            else:
                homework = homeworks[0]
                message = parse_status(homework)
                if last_message != message:
                    send_message(bot, message)
                    last_message = message
                timestamp = response.get("current_date")

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_message != message:
                send_message(bot, message)
                last_message = message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    logging.basicConfig(
        handlers=[logging.StreamHandler(stream=sys.stdout),
                  logging.FileHandler(LOG_FILE_PATH)
                  ],
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
