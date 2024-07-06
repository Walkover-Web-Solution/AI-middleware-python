FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install --trusted-host --no-cache-dir -r req.txt
EXPOSE 8080
CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8080"]