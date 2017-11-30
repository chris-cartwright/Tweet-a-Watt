FROM kennethreitz/pipenv

COPY . /app

CMD python wattcher.py
