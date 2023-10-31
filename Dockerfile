FROM python:3.11

RUN mkdir -p /home/OperChatBot
COPY ./app /home/OperChatBot/app

WORKDIR /home/OperChatBot

RUN pip install -r app/requirements.txt
RUN mkdir db
RUN touch db/botdb.db

CMD ["python", "app/app.py"]
