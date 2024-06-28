FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install playwright
RUN playwright install

EXPOSE 5000

ENV NAME World

CMD ["python", "main.py"]
