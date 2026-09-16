FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN pygbag --build main.py

EXPOSE 8080

CMD ["sh", "-c", "python -m http.server ${PORT:-8080} --directory /app/build/web"]
