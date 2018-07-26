FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -y \
        vim \
        python-pip \
    && rm -rf /var/lib/apt/lists/*

# Make dir for the source
RUN mkdir /app
WORKDIR /app

# Install python deps
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else over
COPY . /app

ENV FLASK_APP app.py

ENTRYPOINT ["flask"]

CMD ["run", "--host=0.0.0.0"]

EXPOSE 5000
