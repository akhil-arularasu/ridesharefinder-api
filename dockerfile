FROM python:3
RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_APP=flask_app.py
# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku			
CMD gunicorn --bind 0.0.0.0:$PORT flask_app:app 
#EXPOSE 5000
#CMD ["python", "flask_app.py"]


