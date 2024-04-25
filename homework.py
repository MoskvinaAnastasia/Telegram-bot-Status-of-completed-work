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


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message,)
        logging.debug(f"Сообщение отправлено в Telegram: {message}")
        return True
    except telegram.TelegramError as error:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {error}")
        return False


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(f"Ошибка запроса: {response.status_code}")
        return response.json()
    except requests.RequestException as error:
        logging.error(f"Ошибка при запросе к API: {error}")
        raise RuntimeError("Ошибка при запросе к API") from error


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
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise ValueError("Отсутствует ключ 'homework_name' в ответе API")
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status, 'Статус работы не определен')
    if verdict == 'Статус работы не определен':
        message = f"Неожиданный статус домашней работы в ответе API: {status}"
        logging.error(message)
        raise ValueError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


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
            logging.debug('Проверка существования новой домашней работы')
            if homeworks:
                logging.info('Найдена домашняя работа')
                if homeworks[0] != last_message:
                    logging.info('Есть новая домашняя работа')
                    try:
                        message_sent = send_message(
                            bot, parse_status(homeworks[0])
                        )
                        if message_sent:
                            last_message = message_sent
                            timestamp = int(time.time())
                    except Exception as error:
                        logging.error(f'Ошибка отправки сообщения '
                                      f'в Telegram: {error}')
                else:
                    logging.debug('Новых домашних работ еще не было')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, f'Произошла ошибка: {error}')
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
