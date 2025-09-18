# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# copy launcher and make it executable; strip CRLF if committed from Windows
COPY start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# default command (fly will override if you use [processes])
CMD ["/app/start.sh"]