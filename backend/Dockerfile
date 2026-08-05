FROM python:3.12

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY data/ /app/data/

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]