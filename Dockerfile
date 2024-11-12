FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install --trusted-host --no-cache-dir -r req.txt
EXPOSE 8080
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "index:app"]
