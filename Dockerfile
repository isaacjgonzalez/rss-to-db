FROM python:3
RUN mkdir -p /data
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade setuptools pip
RUN pip3 install -r requirements.txt
COPY app/ /app/
CMD ["python","-u","./sheduler.py"]
