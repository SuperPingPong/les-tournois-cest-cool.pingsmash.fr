FROM python:3.10.9-alpine

RUN adduser -D worker -h /app
USER worker
WORKDIR /app

ENV PATH="/app/.local/bin:${PATH}"
RUN pip install --user --upgrade pip
COPY --chown=worker:worker requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=worker:worker . .
CMD python main.py