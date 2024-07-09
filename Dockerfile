FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install --trusted-host --no-cache-dir -r req.txt
EXPOSE 8080
CMD ["gunicorn", "index:app", "-k", " uvicorn.workers.UvicornWorker", "--timeout", "90"]