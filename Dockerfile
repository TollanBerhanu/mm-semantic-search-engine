# FROM python:alpine3.18
# FROM python:latest
FROM python:3.10.13-slim-bookworm
WORKDIR /app
COPY . .

# RUN pip install --upgrade pip
# RUN pip freeze
RUN apt-get update && apt-get install -y g++ && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt
# RUN ./install.sh

CMD ["python", "./src/server.py"]

ENV PORT=5555

EXPOSE 5555