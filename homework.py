import telegram
import time
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
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


def check_tokens() -> bool:
    """Проверяем доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message,)
    except Exception as error:
        print(f"Ошибка при отправке сообщения: {error}")


def get_api_answer(timestamp):
    ...


def check_response(response: dict) -> bool:
    """Проверяем ответ API на соответствие документации."""
    if not response:
        message = "В ответе пришел пустой словарь."
        raise KeyError(message)

    if not isinstance(response, dict):
        message = "Тип ответа не соответствует 'dict'."
        raise TypeError(message)

    if 'homeworks' not in response:
        message = "В ответе отсутствует ключ 'homeworks'."
        raise KeyError(message)
    
    if 'current_date' not in response:
        message = "В ответе отсутствует ключ 'current_date'."
        raise KeyError(message)

    if not isinstance(response.get('homeworks'), list):
        message = "Формат ответа не соответствует списку."
        raise TypeError(message)
    
    if not isinstance(response.get('homeworks'), int):
        message = "Формат ответа не соответствует числу."
        raise TypeError(message)
    
    expected_keys = {'date_updated', 'homework_name', 'id', 'lesson_name',
                     'reviewer_comment', 'status'}
    if not set('homeworks'.keys()) == expected_keys:
        raise ValueError("Элемент списка 'homeworks' "
                         "не содержит ожидаемые ключи")


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной
    домашней работе статус этой работы.
    """
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    text = 'Бот начал работу'
    bot.send_message(TELEGRAM_CHAT_ID, text)
    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
