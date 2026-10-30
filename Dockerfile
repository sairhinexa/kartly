# Kartly -- security training target.
# Build:  docker build -t kartly-lab .
# Run:    docker run --rm -p 127.0.0.1:5000:5000 kartly-lab
# (compose keeps it bound to localhost; never expose it to a network)
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Inside the container we must listen on all interfaces; the published port is
# mapped back to 127.0.0.1 on the host (see docker-compose.yml / run command).
ENV KARTLY_HOST=0.0.0.0
ENV KARTLY_PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]
