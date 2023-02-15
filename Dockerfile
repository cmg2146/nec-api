FROM python:3.11-slim

# install dependencies
WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

# copy app
WORKDIR /app/src
COPY ./src ./

WORKDIR /app/src/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
