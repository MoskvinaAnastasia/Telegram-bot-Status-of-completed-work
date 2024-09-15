## Telegram bot для проверки статуса домашней работы

## Стек использованных технологий
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

## Описание проекта
- Раз в 10 минут опрашивает API сервиса Telegram bot для проверки статуса домашней работы и проверяет статус отправленной на ревью домашней работы.
- При обновлении статуса анализирует ответ API и отправляет вам соответствующее уведомление в Telegram.
- Логгирует свою работу и сообщает вам о важных проблемах сообщением в Telegram.

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```bash
git clone https://github.com/MoskvinaAnastasia/homework_bot
```
```bash
cd homework_bot/
```
Создать файл .env в этой директории и укажите собственные токены:
```bash
PRACTICUM_TOKEN = токен Яндекс практикум.
TELEGRAM_TOKEN = токен вашего бота Telegram полученный от BotFather.
TELEGRAM_CHAT_ID = id вашего чата в Telegram.
```

### Получаем токены:
- Зарегистрируйте бота в BotFather:
[Регистрация бота и получение токена](https://t.me/BotFather)

- Получите токен в ЯндексПрактикум:
[Получить токен](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a)

- Получите id своего чата у бота Userinfobot:
[Получить свой id](https://t.me/userinfobot)

## Автор проекта
[MoskvinaAnastasia](https://github.com/MoskvinaAnastasia/)