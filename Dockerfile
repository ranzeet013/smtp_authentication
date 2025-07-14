FROM python:3.10-slim

WORKDIR /app

COPY . .



# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001

CMD ["python", "src/main.py"]
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]