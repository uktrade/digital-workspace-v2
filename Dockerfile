FROM python:3.9-buster

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSTARTUP=.pythonrc.py

WORKDIR /app
COPY requirements/dev.txt requirements/dev.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir honcho 
RUN pip install --no-cache-dir -r requirements/dev.txt

RUN curl -fsSL https://deb.nodesource.com/setup_19.x | bash - &&\
   apt-get install -y nodejs

COPY . ./

RUN npm install
RUN npm run build

CMD honcho start 
