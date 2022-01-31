FROM python:alpine
WORKDIR /code
EXPOSE 8080
COPY ./src .
COPY main.py .
CMD ["python", "main.py"]