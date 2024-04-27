import logging
import os
import sys
import time
from http import HTTPStatus


from dotenv import load_dotenv
import requests
import telegram


load_dotenv()

logging.basicConfig(
    handlers=[logging.StreamHandler(stream=sys.stdout),
              logging.FileHandler('logging_bot.log')
              ],
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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


def check_tokens() -> bool:
    """Проверяем доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.Bot, message: str) -> bool:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message,)
        logging.debug(f"Сообщение отправлено в Telegram: {message}")
    except telegram.TelegramError as error:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {error}")
    else:
        logging.debug('Статус отправлен в telegram')


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(f"Ошибка запроса: {response.status_code}")
        return response.json()
    except requests.RequestException as error:
        text = "Ошибка при запросе к API"
        logging.error(f"{text}: {error}")
        raise RuntimeError(f"{text}: {error}") from error


def check_response(response: dict) -> bool:
    """Проверяем ответ API на соответствие документации."""
    if not response:
        message = "В ответе пришел пустой словарь."
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response, dict):
        message = "Тип ответа не соответствует 'dict'."
        logging.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        message = "В ответе отсутствует ключ 'homeworks'."
        logging.error(message)
        raise KeyError(message)

    if 'current_date' not in response:
        message = "В ответе отсутствует ключ 'current_date'."
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response.get('homeworks'), list):
        message = "Формат ответа не соответствует списку."
        logging.error(message)
        raise TypeError(message)

    if not isinstance(response.get('current_date'), int):
        message = "Формат ответа не соответствует числу."
        logging.error(message)
        raise TypeError(message)

    homeworks = response.get('homeworks')
    if homeworks is None:
        raise ValueError('Ответ API не содержит ключ "homeworks"')


def parse_status(homework: dict) -> str:
    """Извлекает статус, возвращает в Telegram строку статуса."""
    if not isinstance(homework, dict):
        raise TypeError('Полученный аргумент должен быть словарем.')
    logging.debug('Получение статуса домашней работы')
    status = homework.get('status')
    if 'status' not in homework:
        message = 'Не найден ключ "status" в словаре домашней работы.'
        logging.error(message)
        raise KeyError(message)
    verdict = HOMEWORK_VERDICTS.get(status)
    if status not in HOMEWORK_VERDICTS:
        message = f'Статус {status} не найден в HOMEWORK_VERDICTS.'
        logging.error(message)
        raise KeyError(message)
    name = homework.get('homework_name')
    if 'homework_name' not in homework:
        message = 'Не найден ключ "homework_name" в словаре домашней работы.'
        logging.error(message)
        raise KeyError(message)
    return f'Изменился статус проверки работы "{name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Программа останавливается. Отсутствуют токены'
        logging.critical(message)
        sys.exit(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    text = 'Я всего лишь машина, только имитация жизни, ' \
           'но давай проверим твою работу'
    bot.send_message(TELEGRAM_CHAT_ID, text)
    last_message = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug("Домашних работ нет.")
            else:
                index = 0
                homework = homeworks[index]
                message = parse_status(homework)
                if last_message != message:
                    send_message(bot, message)
                    last_message = message
                timestamp = response.get("current_date")

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_message != message:
                try:
                    send_message(bot, message)
                    last_message = message
                except Exception as send_error:
                    logging.error(f'Ошибка при отправке сообщения: {send_error}')
                finally:
                    last_message = message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()