find-me-flat-bot
================

WinServer
---------

1. ubuntu on windows
https://itisgood.ru/2019/02/26/kak-zapustit-linux-na-windows-server-2019-s-wsl/

2. ssh
https://winitpro.ru/index.php/2019/10/17/windows-openssh-server/
https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement



Ботик для telegram, который будет мониторить cian и скидывать вам новые объявления в Telegram.

Как настроить:
1. Заводим своего бота в телеграме, [@BotFather](https://t.me/BotFather) вам в помощь. Главное `/newbot` - получить токен.

https://t.me/find_me_flat_27052026_bot

2. В любом облаке заводим инстанс с Docker. Это можно сделать за пару кликов в [DigitalOcean](https://m.do.co/c/f099e32edcfe).
3. Дальше все просто:

```bash
git clone git@github.com:persidskiy/find-me-flat-bot.git
cd find-me-flat-bot

docker build . -t "find-me-flat-bot"

# в обычном режиме:
docker run -t -e TG_BOT_TOKEN="<token>" find-me-flat-bot:latest
docker run -t -e DEBUG=1 -e VERBOSE=1 find-me-flat-bot:latest
# в режиме демона
docker run -d -e TG_BOT_TOKEN="<token>" find-me-flat-bot:latest
```

отладка
```bash
git clone git@github.com:persidskiy/find-me-flat-bot.git
cd find-me-flat-bot

# сделать virtenv 
python -m venv env
# активировать
source env/bin/activate
# поставить зависимости проекта
pip install -r requirements.txt
# для винды
pip install --prefer-binary -r requirements.txt

python bot.py
# выйти
deactivate
```




Ваш бот готов, можно написать ему `/ping`, он должен ответить.

Команды
-------

```
/start <url> - Начать наблюдать за объявлениями по этому url
/stop - Закончить наблюдение
/ping - Проверить, что бот жив. За одно он вернет текущий наблюдаемый URL.
```

URL для парсинга - URL страницы на Cian со всеми примененными фильтрами и отображением в виде списка (это важно) 
[пример](https://www.cian.ru/cat.php?currency=2&deal_type=rent&district%5B0%5D=21&engine_version=2&maxprice=60000&offer_type=flat&room1=1&room2=1&totime=-2&type=4&wp=1)


[савок до 60](https://www.cian.ru/cat.php?bbox=55.78360858025065%2C37.51609532314447%2C55.81305300302533%2C37.622525376855414&currency=2&deal_type=rent&engine_version=2&in_polygon%5B1%5D=37.5819275_55.8084885%2C37.5769493_55.8090689%2C37.5723144_55.8089721%2C37.5666496_55.8081016%2C37.5613281_55.8068441%2C37.5563499_55.8051998%2C37.5529167_55.8037488%2C37.5512001_55.8012339%2C37.5529167_55.7980419%2C37.5544616_55.795527%2C37.5558349_55.7929153%2C37.5566932_55.7905939%2C37.5590965_55.7884658%2C37.563388_55.7878855%2C37.5700828_55.787692%2C37.5743744_55.787692%2C37.5796959_55.7875953%2C37.5839874_55.7886593%2C37.585704_55.7910775%2C37.5865623_55.7936891%2C37.5874206_55.7963975%2C37.5874206_55.7990092%2C37.5860473_55.8015241%2C37.5850174_55.8038456%2C37.5850174_55.8062638%2C37.5822708_55.8081983%2C37.5819275_55.8084885&maxprice=60000&offer_type=flat&polygon_name%5B1%5D=%D0%92%D1%8B%D0%B4%D0%B5%D0%BB%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F+%D0%BE%D0%B1%D0%BB%D0%B0%D1%81%D1%82%D1%8C&region=1&type=4&saved_search_id=58609849)