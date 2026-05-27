# FROM --platform=linux/amd64 python:3.9
FROM python:3.9

RUN apt update
RUN apt install -y chromium
# RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
# RUN rm google-chrome-stable_current_amd64.deb

RUN apt install -y chromium-driver
# RUN apt install -y chromium-chromedriver

RUN apt install -y wget gnupg xvfb libxi6 \
    unzip

RUN apt clean && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /requirements.txt
RUN pip install --prefer-binary -r requirements.txt

ADD . /
# RUN rm -rf data/*
VOLUME [ "/data" ]

RUN echo "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && python bot.py" > /entrypoint.sh
CMD ["sh", "/entrypoint.sh"]