from fastapi import APIRouter
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(database=os.getenv('DATABASE_NAME'),
                        host=os.getenv('DATABASE_HOST'),
                        user=os.getenv('DATABASE_USER'),
                        password=os.getenv('DATABASE_PASSWORD'),
                        port=os.getenv('DATABASE_PORT'))

cursor = conn.cursor()

router = APIRouter()
