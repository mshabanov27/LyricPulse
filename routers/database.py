from fastapi import APIRouter
import psycopg2


conn = psycopg2.connect(database="LyricPulse",
                        host="localhost",
                        user="YOUR_USER",
                        password="YOUR_PASSWORD",
                        port="YOUR_PORT")

cursor = conn.cursor()


router = APIRouter()
