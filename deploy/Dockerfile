FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libmysqlclient-dev \
    default-libmysqlclient-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    netcat \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./hhcc /app/
COPY ./requirements.txt /app/

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN cat > /app/wait-for-mysql.sh <<'SH'
#!/bin/bash
set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd
SH

RUN chmod +x /app/wait-for-mysql.sh

EXPOSE 8000

RUN cat > /app/start.sh <<'SH'
#!/bin/bash
set -e

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-3306}

/app/wait-for-mysql.sh "$DB_HOST" "$DB_PORT" echo "Base de datos lista"

python3 manage.py migrate --noinput
python3 manage.py runserver 0.0.0.0:8000
SH

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
