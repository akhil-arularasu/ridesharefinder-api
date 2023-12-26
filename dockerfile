FROM python:3
WORKDIR /backend
COPY ./requirements.txt /backend
RUN pip install -r ./requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "flask_app.py"]