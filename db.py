import psycopg2
from decouple import config

conn = psycopg2.connect(
    host= config('DB_HOST', default='localhost'),
    port= config('DB_PORT', default='5432'),
    database= config('DB_NAME'),
    user= config('DB_USER'),
    password= config('DB_PASSWORD')
)
