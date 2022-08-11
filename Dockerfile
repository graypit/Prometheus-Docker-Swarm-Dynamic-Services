FROM python:3.8.3-alpine
MAINTAINER Habib Guliyev <hguliyev@gptlab.io>
WORKDIR /app
RUN pip install --upgrade pip
COPY . .
RUN python3 -m pip install -r requirements.txt
#ensures that /var/run/docker.sock exists
RUN touch /var/run/docker.sock
#changes the ownership of /var/run/docker.sock
RUN chown root:root /var/run/docker.sock
ENTRYPOINT [ "python", "-u", "app.py" ]