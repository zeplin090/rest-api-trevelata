FROM python:3.13-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /crud-api

# Запрещаем Python писать файлы .pyc на диск и буферизировать stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Команда для запуска (uvicorn слушает порт 8000 на всех интерфейсах)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]