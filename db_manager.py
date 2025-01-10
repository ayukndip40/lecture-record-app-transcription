import mysql.connector

class DBManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = self.connect()

    def connect(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )

    def create_database(self):
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        cursor.close()
        self.connection.database = self.database  # Switch to the new database

    def create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                subject VARCHAR(255),
                category VARCHAR(255),
                audio_path VARCHAR(255),
                transcription_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                audio_id INT,
                action ENUM('upload', 'record', 'transcribe'),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id),
                FOREIGN KEY (audio_id) REFERENCES audio(id)
            )
        """)

        self.connection.commit()
        cursor.close()

    def save_user(self, username, password):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, password))
        self.connection.commit()
        cursor.close()

    def verify_user(self, username, password):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        return user

    def save_audio(self, user_id, subject, category, audio_path, transcription_path):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO audio (user_id, subject, category, audio_path, transcription_path) 
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, subject, category, audio_path, transcription_path))
        audio_id = cursor.lastrowid
        self.connection.commit()
        cursor.close()
        return audio_id

    def get_user_audios(self, user_id):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM audio WHERE user_id = %s", (user_id,))
        audios = cursor.fetchall()
        cursor.close()
        return audios

    def save_transaction(self, user_id, audio_id, action):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO transaction (user_id, audio_id, action) 
            VALUES (%s, %s, %s)
        """, (user_id, audio_id, action))
        self.connection.commit()
        cursor.close()

    def get_audio(self, audio_id):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM audio WHERE id = %s", (audio_id,))
        audio = cursor.fetchone()
        cursor.close()
        return audio

    def close_connection(self):
        self.connection.close()
