# club-managmenet-sys

# This web-based app was developed to provide significant features for clubs managment.

# The project consists of two main services: playgrounds reservation management functionalities - acedimic subscriptions management

# To begin with the app you must follow the following conf steps:
- create a virtualenv
    On Windows:
      python -m venv myenv
      myenv\Scripts\activate
    On macOS and Linux:
      python3 -m venv myenv
      source myenv/bin/activate


- install requirements.txt file => pip install -r requirements.txt

- create the necessary migrations and migrate to the database. apply all the following commands:
  python manage.py makemigrations users
  python manage.py makemigrations reservations
  python manage.py makemigrations subscriptions
  python manage.py makemigrations middleapp

  python manage.py migrate users
  python manage.py migrate reservations
  python manage.py migrate subscriptions
  python manage.py migrate middleapp
  python manage.py migrate

- create superuser credentials => python manage.py createsuperuser

- run the server and access with your recently created credentials =>python manage.py createsuperuser
