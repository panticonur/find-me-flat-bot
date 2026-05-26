FROM python:3.9

ADD requirements.txt /requirements.txt
RUN pip install -r requirements.txt

ADD . /

VOLUME [ "/data" ]

CMD ["python", "bot.py"]