"""
WSGI entry point for production deployment
Use with Gunicorn: gunicorn wsgi:application
"""
from application import application

if __name__ == "__main__":
    application.run()
