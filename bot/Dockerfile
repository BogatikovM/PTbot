FROM python:3.11-alpine

WORKDIR /app

EXPOSE 3030

RUN apk add --no-cache postgresql-dev gcc musl-dev linux-headers

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "tgbot.py"]
