## Homework telegram bot

### Homework telegram bot - это бот для телеграм, который оповещает о статусах проверки домашнего задания в сервисе Яндекс Практикум.

### Запуск в режиме разработчика:

Создание и активация виртуального окружения:
```bash
python3 -m venv venv # MacOS и Linux
python -m venv venv # Windows
```
```bash
source venv/bin/activate # MacOS и Linux
source venv\Scripts\activate # Windows
```
Установка зависимостей из файла requirements.txt:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### Заполнить переменные в файле .env:

```bash
PRACTICUM_TOKEN = # ваш токен с сервиса ЯП
TELEGRAM_TOKEN = # токен вашего бота телеграм
TELEGRAM_CHAT_ID = # ваш id в телеграм
```

Автор: [Семен Ванюшин](https://github.com/semenvanyushin)
