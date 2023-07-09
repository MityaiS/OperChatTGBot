FROM python

RUN mkdir -p /home/OperChatBot
COPY . /home/OperChatBot

WORKDIR /home/OperChatBot

RUN pip install -r requirements.txt
RUN touch botdb.db

CMD ["python", "app.py"]
