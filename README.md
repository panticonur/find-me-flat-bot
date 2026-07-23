find-me-flat-bot
================

Telegram бот мониторит cian.ru и сообщает о новых объявлениях.
Боту задается ссылка на страницу результатов поиска квартир на cian.
Интервал поиска настраивается, по-умолчанию каждые 600 секунд.
Бот следит только за одной страницей,- для мониторинга нескольких страниц нужно 
создать несколько экземпляторов. 
Каждый экземплятор состоит из пары зарегистрированного Telegram-бота и docker контейнера связанных токеном.

Команды
-------

* ```/start``` Начать наблюдать за объявлениями.
* ```/url <http://cian.ru/...>``` Задать URL для парсинга страницы результатами поиска на Cian со всеми примененными фильтрами. **Важно чтобы отображение результатов было в виде списка.**
[<u>пример</u>](https://www.cian.ru/cat.php?currency=2&deal_type=rent&district%5B0%5D=21&engine_version=2&maxprice=60000&offer_type=flat&room1=1&room2=1&totime=-2&type=4&wp=1)
[<u>область на карте</u>](https://www.cian.ru/cat.php?bbox=55.78360858025065%2C37.51609532314447%2C55.81305300302533%2C37.622525376855414&currency=2&deal_type=rent&engine_version=2&in_polygon%5B1%5D=37.5819275_55.8084885%2C37.5769493_55.8090689%2C37.5723144_55.8089721%2C37.5666496_55.8081016%2C37.5613281_55.8068441%2C37.5563499_55.8051998%2C37.5529167_55.8037488%2C37.5512001_55.8012339%2C37.5529167_55.7980419%2C37.5544616_55.795527%2C37.5558349_55.7929153%2C37.5566932_55.7905939%2C37.5590965_55.7884658%2C37.563388_55.7878855%2C37.5700828_55.787692%2C37.5743744_55.787692%2C37.5796959_55.7875953%2C37.5839874_55.7886593%2C37.585704_55.7910775%2C37.5865623_55.7936891%2C37.5874206_55.7963975%2C37.5874206_55.7990092%2C37.5860473_55.8015241%2C37.5850174_55.8038456%2C37.5850174_55.8062638%2C37.5822708_55.8081983%2C37.5819275_55.8084885&maxprice=60000&offer_type=flat&polygon_name%5B1%5D=%D0%92%D1%8B%D0%B4%D0%B5%D0%BB%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F+%D0%BE%D0%B1%D0%BB%D0%B0%D1%81%D1%82%D1%8C&region=1&type=4&saved_search_id=58609849)
* ```/url``` Вернуть текущий наблюдаемый URL.
* ```/scan``` Выполнить поиск объявлений.
* ```/gap <seconds>``` Задать интервал поиска объявлений в секундах.
* ```/reset``` Сбросить список найденных объявлений.
* ```/status``` Вернет оставшее время до обновления поиска.

Установка
---------
1. Регистрируйте своего бота в телеграме с помощью [@BotFather](https://t.me/BotFather).
Командой `/newbot` задайте адрес бота <https://t.me/..._bot> и получите токен. Сохраните токен в секрете.

2. В любом облаке заводим инстанс с Docker.
Для запуска на локальной машине установить Docker Desktop.
3. 
```bash
git clone git@github.com:panticonur/find-me-flat-bot.git
cd find-me-flat-bot

docker build . -t "find-me-flat-bot"

# в обычном режиме:
docker run -t -e TG_BOT_TOKEN="<token>" find-me-flat-bot:latest

# в режиме демона
docker run -d -e TG_BOT_TOKEN="<token>" find-me-flat-bot:latest
```

Ваш бот готов, можно написать ему `/status`, он должен ответить.

Разработка
==========
```bash
git clone git@github.com:panticonur/find-me-flat-bot.git
cd find-me-flat-bot

# сделать virtenv 
python -m venv env

# активировать
source env/bin/activate
# или для windows
source env/Scripts/activate

# поставить зависимости проекта
pip install -r requirements.txt
# или для windows
pip install --prefer-binary -r requirements.txt

python bot.py

# выйти
deactivate
```

При ошибке на первом запуске отладчика, выполнить первую команду из терминала:
```
cmd /C "c:\Users\admin\Desktop\find-me-flat-bot/env/Scripts/python.exe c:\Users\admin\.vscode\extensions\ms-python.debugpy-2026.6.0-win32-x64\bundled\libs\debugpy\launcher 54669 -- C:\Users\admin\Desktop\find-me-flat-bot/bot.py "
```

```bash
docker build --no-cache --progress=plain . -t "find-me-flat-bot"
docker run -t -e TG_BOT_TOKEN="<token>" -e DEBUG=1 -e VERBOSE=1 find-me-flat-bot:latest

# Your image is built and ready. The image find-me-flat-bot:latest is now available on your system. The build completed with a minor warning about the --platform flag in the FROM instruction, which is informational only — the image built successfully and will work.

# To run the container:

docker run -v /app/data find-me-flat-bot
# Or if you want to mount a local directory for data persistence:
docker run -v C:\path\to\local\data:/app/data find-me-flat-bot
```

WinServer
---------

1. ubuntu on windows
https://itisgood.ru/2019/02/26/kak-zapustit-linux-na-windows-server-2019-s-wsl/

2. ssh
https://winitpro.ru/index.php/2019/10/17/windows-openssh-server/
https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement