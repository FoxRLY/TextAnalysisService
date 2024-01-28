# Используем базовый образ с Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в /src
WORKDIR /src

# Устанавливаем зависимости, включая libpq-dev
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем код в рабочую директорию
COPY ./ .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем сервер на порту 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

