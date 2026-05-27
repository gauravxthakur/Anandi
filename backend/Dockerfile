FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu118

COPY . .

EXPOSE 7860

RUN useradd -m -u 1000 app
USER app

CMD ["uvicorn", "auto_fetal_biometry:app", "--host", "0.0.0.0", "--port", "7860"]