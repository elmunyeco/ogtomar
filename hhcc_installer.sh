#!/bin/bash

# Script de instalación para el proyecto HHCC (Historias Clínicas Cardiología)
# Implementación con Docker para la aplicación y la base de datos
# Para Ubuntu 20.04 LTS en DigitalOcean

set -e  # Detener el script si hay un error

# Colores para mejor legibilidad
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con formato
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Verificar que se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
    error "Este script debe ejecutarse como root. Intente con sudo."
fi

# Configuración de variables
REPO_URL="https://github.com/elmunyeco/ogtomar.git"
BRANCH="master"
PROJECT_DIR="/opt/hhcc"
MYSQL_ROOT_PASSWORD="Corbis5"
MYSQL_DATABASE="cardioprieto"
MYSQL_USER="cardioprieto"
MYSQL_PASSWORD="Corbis5"

log "Iniciando instalación del proyecto HHCC con Docker..."

# Actualizar el sistema
log "Actualizando el sistema..."
apt-get update
apt-get upgrade -y

# Instalar dependencias básicas
log "Instalando dependencias básicas..."
apt-get install -y \
    git \
    curl \
    wget \
    apt-transport-https \
    ca-certificates \
    gnupg-agent \
    software-properties-common

# Instalar Docker
log "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
    log "Docker instalado correctamente."
else
    log "Docker ya está instalado."
fi

# Instalar Docker Compose
log "Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log "Docker Compose instalado correctamente."
else
    log "Docker Compose ya está instalado."
fi

# Crear directorio del proyecto y clonar el repositorio
log "Preparando el directorio del proyecto..."
if [ ! -d "$PROJECT_DIR" ]; then
    log "Creando directorio $PROJECT_DIR y clonando repositorio..."
    mkdir -p "$PROJECT_DIR"
    git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
else
    warn "El directorio $PROJECT_DIR ya existe."
    
    # Verificar si es un repositorio git válido
    if [ -d "$PROJECT_DIR/.git" ]; then
        log "Actualizando repositorio existente..."
        cd "$PROJECT_DIR"
        git fetch
        git checkout "$BRANCH"
        git pull
    else
        warn "No es un repositorio git válido. Limpiando y clonando nuevamente..."
        # Hacer backup del directorio existente
        BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d%H%M%S)"
        mv "$PROJECT_DIR" "$BACKUP_DIR"
        log "Se ha creado un backup en $BACKUP_DIR"
        
        # Clonar el repositorio
        mkdir -p "$PROJECT_DIR"
        git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
    fi
fi

# Verificar que existe el archivo de la base de datos
if [ ! -f "$PROJECT_DIR/nuevo_cardioprieto.sql.gz" ]; then
    error "No se encontró el archivo de base de datos nuevo_cardioprieto.sql.gz en la raíz del proyecto."
fi

# Crear el Dockerfile para la aplicación
log "Creando Dockerfile para la aplicación..."
cat > "$PROJECT_DIR/Dockerfile" << 'EOF'
FROM ubuntu:20.04

# Evitar interacciones durante la instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Instalar dependencias
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY ./hhcc /app/
COPY ./requirements.txt /app/

# Instalar dependencias de Python
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Crear un script de espera para la base de datos
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
host="$1"\n\
port="$2"\n\
shift 2\n\
cmd="$@"\n\
\n\
until nc -z "$host" "$port"; do\n\
  >&2 echo "MySQL is unavailable - sleeping"\n\
  sleep 1\n\
done\n\
\n\
>&2 echo "MySQL is up - executing command"\n\
exec $cmd' > /app/wait-for-mysql.sh

RUN chmod +x /app/wait-for-mysql.sh

# Exponer el puerto
EXPOSE 8000

# Comando para iniciar la aplicación
# Script para configurar la base de datos y ejecutar la aplicación
RUN echo '#!/bin/bash\n\
# Esperar a que la base de datos esté disponible\n\
/app/wait-for-mysql.sh db 3306 echo "Base de datos lista"\n\
\n\
# Actualizar configuración de la base de datos en settings.py\n\
SETTINGS_FILE="/app/hhcc/settings.py"\n\
if [ -f "$SETTINGS_FILE" ]; then\n\
    sed -i "s/'\''ENGINE'\'': '\''.*'\''/'\'ENGINE\': \'\''django.db.backends.mysql\'\''/" "$SETTINGS_FILE"\n\
    sed -i "s/'\''NAME'\'': '\''.*'\''/'\'NAME\': \'\''$DB_NAME\'\''/" "$SETTINGS_FILE"\n\
    sed -i "s/'\''USER'\'': '\''.*'\''/'\'USER\': \'\''$DB_USER\'\''/" "$SETTINGS_FILE"\n\
    sed -i "s/'\''PASSWORD'\'': '\''.*'\''/'\'PASSWORD\': \'\''$DB_PASSWORD\'\''/" "$SETTINGS_FILE"\n\
    sed -i "s/'\''HOST'\'': '\''.*'\''/'\'HOST\': \'\''$DB_HOST\'\''/" "$SETTINGS_FILE"\n\
    sed -i "s/'\''PORT'\'': '\''.*'\''/'\'PORT\': \'\''$DB_PORT\'\''/" "$SETTINGS_FILE"\n\
    echo "Configuración de la base de datos actualizada en settings.py"\n\
else\n\
    echo "ADVERTENCIA: No se encontró el archivo settings.py"\n\
fi\n\
\n\
# Ejecutar migraciones\n\
python3 manage.py migrate --noinput\n\
\n\
# Ejecutar el servidor de desarrollo\n\
python3 manage.py runserver 0.0.0.0:8000\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
EOF

# Configurar Docker Compose
log "Configurando Docker Compose..."
cat > "$PROJECT_DIR/docker-compose.yml" << EOF
version: '3'

services:
  db:
    image: mariadb:10.5
    container_name: hhcc_mariadb
    restart: always
    environment:
      MARIADB_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MARIADB_DATABASE: ${MYSQL_DATABASE}
      MARIADB_USER: ${MYSQL_USER}
      MARIADB_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3307:3306"
    volumes:
      - mariadb_data:/var/lib/mysql
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    networks:
      - hhcc_network

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hhcc_app
    restart: always
    depends_on:
      - db
    ports:
      - "8000:8000"
    volumes:
      - ./hhcc:/app
    environment:
      - DB_HOST=db
      - DB_PORT=3306
      - DB_NAME=${MYSQL_DATABASE}
      - DB_USER=${MYSQL_USER}
      - DB_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
    networks:
      - hhcc_network

networks:
  hhcc_network:
    driver: bridge

volumes:
  mariadb_data:
EOF

# Crear script para actualizar el settings.py
log "Creando script para actualizar settings.py..."
cat > "$PROJECT_DIR/update_settings.sh" << 'EOF'
#!/bin/bash

SETTINGS_FILE="/app/hhcc/settings.py"

# Verificar que el archivo existe
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "Error: No se encontró el archivo settings.py"
    exit 1
fi

# Backup del archivo
cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"

# Actualizar la configuración de la base de datos
sed -i "s/'ENGINE': '.*'/'ENGINE': 'django.db.backends.mysql'/" "$SETTINGS_FILE"
sed -i "s/'NAME': '.*'/'NAME': '$DB_NAME'/" "$SETTINGS_FILE"
sed -i "s/'USER': '.*'/'USER': '$DB_USER'/" "$SETTINGS_FILE"
sed -i "s/'PASSWORD': '.*'/'PASSWORD': '$DB_PASSWORD'/" "$SETTINGS_FILE"
sed -i "s/'HOST': '.*'/'HOST': '$DB_HOST'/" "$SETTINGS_FILE"
sed -i "s/'PORT': '.*'/'PORT': '$DB_PORT'/" "$SETTINGS_FILE"

echo "Archivo settings.py actualizado correctamente."
EOF

chmod +x "$PROJECT_DIR/update_settings.sh"

# Crear script para importar la base de datos después de que MariaDB esté listo
log "Creando script para importar la base de datos..."
cat > "$PROJECT_DIR/import_database.sh" << EOF
#!/bin/bash

echo "Esperando a que MariaDB esté listo..."
sleep 30

echo "Restaurando la base de datos desde nuevo_cardioprieto.sql.gz..."
gunzip -c /tmp/nuevo_cardioprieto.sql.gz | mariadb -h db -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}

echo "Base de datos restaurada correctamente."
EOF

chmod +x "$PROJECT_DIR/import_database.sh"

# Crear un Dockerfile adicional para importar la base de datos
log "Creando Dockerfile para importar la base de datos..."
cat > "$PROJECT_DIR/Dockerfile.db-import" << EOF
FROM mariadb:10.5

RUN apt-get update && apt-get install -y \
    netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY nuevo_cardioprieto.sql.gz /tmp/
COPY import_database.sh /tmp/

CMD ["/tmp/import_database.sh"]
EOF

# Añadir el servicio de importación de base de datos a docker-compose.yml
log "Actualizando docker-compose.yml con el servicio de importación de base de datos..."
cat >> "$PROJECT_DIR/docker-compose.yml" << EOF

  db-import:
    build:
      context: .
      dockerfile: Dockerfile.db-import
    container_name: hhcc_db_import
    depends_on:
      - db
    networks:
      - hhcc_network
EOF

# Iniciar los servicios con Docker Compose
log "Iniciando los servicios con Docker Compose..."
cd "$PROJECT_DIR"
docker-compose up -d

# Esperar a que los servicios estén listos
log "Esperando a que los servicios estén listos..."
sleep 30

# Crear superusuario (opcionalmente)
log "¿Desea crear un superusuario para Django? (s/n)"
read -r CREATE_SUPERUSER

if [[ "$CREATE_SUPERUSER" =~ ^[Ss]$ ]]; then
    log "Creando superusuario..."
    docker exec -it hhcc_app python3 manage.py createsuperuser
fi

# Resumen final
log "==================================================="
log "Instalación completada con éxito!"
log "==================================================="
log "URL de la aplicación: http://$(hostname -I | awk '{print $1}'):8000"
log "MariaDB está disponible en el puerto 3307"
log "Directorio del proyecto: $PROJECT_DIR"
log "Base de datos MariaDB: $MYSQL_DATABASE"
log "Usuario de MariaDB: $MYSQL_USER"
log "==================================================="
log "Para gestionar los contenedores:"
log "  cd $PROJECT_DIR && docker-compose ps"
log "  cd $PROJECT_DIR && docker-compose logs -f"
log "  cd $PROJECT_DIR && docker-compose restart"
log "==================================================="
