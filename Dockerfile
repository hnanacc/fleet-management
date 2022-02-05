FROM python:alpine
WORKDIR /code
COPY . .
RUN ["python", "--version"]
CMD ["python", "main.py"]