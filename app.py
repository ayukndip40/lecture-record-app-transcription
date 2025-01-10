import os
from flask import Flask, request, render_template, redirect, session
from audio_processor import AudioProcessor
from db_manager import DBManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# Initialize the audio processor and database manager
audio_processor = AudioProcessor()
db_manager = DBManager('localhost', 'root', '', 'trans')  # Adjust as necessary

# Initialize database and tables
def initialize_database():
    db_manager.create_database()  # Create the database if it doesn't exist
    db_manager.create_tables()     # Create the tables if they don't exist

# Call the function to set up the database when the app starts
initialize_database()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db_manager.verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = username
            return redirect('/dashboard')
        else:
            return "Invalid username or password", 401

    return render_template('login.html')  # Render the updated login.html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_manager.save_user(username, password)
        return redirect('/login')

    return render_template('register.html')  # Render the new register.html

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    username = session['username']
    audios = db_manager.get_user_audios(user_id)
    return render_template('dashboard.html', username=username, audios=audios)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'user_id' not in session:
        return redirect('/login')

    audio_file = request.files['audio']
    uploads_dir = 'uploads'
    os.makedirs(uploads_dir, exist_ok=True)
    temp_transcription_dir = 'temp_audio_files'
    os.makedirs(temp_transcription_dir, exist_ok=True)

    specified_filename = audio_file.filename.strip()
    audio_file_path = os.path.join(uploads_dir, specified_filename)
    audio_file.save(audio_file_path)

    transcription = audio_processor.audio_to_text(audio_file_path)
    transcription_filename = os.path.splitext(specified_filename)[0] + '.txt'
    transcription_file_path = os.path.join(temp_transcription_dir, transcription_filename)

    with open(transcription_file_path, 'w') as transcription_file:
        transcription_file.write(transcription)

    user_id = session['user_id']
    subject = request.form['subject']
    category = request.form['category']

    audio_id = db_manager.save_audio(user_id, subject, category, audio_file_path, transcription_file_path)
    db_manager.save_transaction(user_id, audio_id, 'upload')

    return redirect(f'/transcription/{audio_id}')

@app.route('/record', methods=['POST'])
def record_audio():
    if 'user_id' not in session:
        return redirect('/login')

    filename = request.form.get('filename', 'recorded_audio.wav').strip()
    audio_processor.record_audio(filename)

    transcription = audio_processor.audio_to_text(filename)
    transcription_filename = os.path.splitext(filename)[0] + '.txt'
    transcription_file_path = os.path.join('temp_audio_files', transcription_filename)

    with open(transcription_file_path, 'w') as f:
        f.write(transcription)

    user_id = session['user_id']
    subject = "Recorded Audio"
    category = "General"

    audio_id = db_manager.save_audio(user_id, subject, category, filename, transcription_file_path)
    db_manager.save_transaction(user_id, audio_id, 'record')

    return redirect(f'/transcription/{audio_id}')

@app.route('/transcription/<int:audio_id>')
def transcription(audio_id):
    if 'user_id' not in session:
        return redirect('/login')

    audio = db_manager.get_audio(audio_id)
    if audio and audio['user_id'] == session['user_id']:
        with open(audio['transcription_path'], 'r') as file:
            transcription = file.read()
        return render_template('transcription.html', transcription=transcription, audio=audio)

    return redirect('/dashboard')

@app.route('/play_audio/<int:audio_id>')
def play_audio(audio_id):
    if 'user_id' not in session:
        return redirect('/login')

    audio = db_manager.get_audio(audio_id)
    if audio and audio['user_id'] == session['user_id']:
        audio_extension = os.path.splitext(audio['audio_path'])[1].lower()
        mime_type = 'audio/mpeg' if audio_extension == '.mp3' else 'audio/wav' if audio_extension == '.wav' else 'audio/ogg'
        return render_template('play_audio.html', audio_path=audio['audio_path'], mime_type=mime_type)

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/close')
def close_db():
    db_manager.close_connection()
    return "Database connection closed!"

if __name__ == '__main__':
    app.run(debug=True)
