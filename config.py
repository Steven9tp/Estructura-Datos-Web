import os

class Config:
    SECRET_KEY = 'u_ride_key_2026'
    # Esta es la línea que estabas pegando en la terminal:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/u_ride_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False