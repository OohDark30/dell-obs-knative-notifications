FROM python:3.9-alpine

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5002

ENTRYPOINT [ "python" ]

CMD [ "dell_obs_knative_notifications.py" ]
