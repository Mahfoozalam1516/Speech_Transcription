from flask import Flask, render_template, request, jsonify
import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'  # Use /tmp for writable storage in Render
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is valid
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Initialize Deepgram client
            deepgram = DeepgramClient(os.getenv('DEEPGRAM_API_KEY'))

            # Read file and prepare payload
            with open(filepath, 'rb') as audio_file:
                buffer_data = audio_file.read()
            
            payload: FileSource = {
                "buffer": buffer_data,
            }

            # Configure Deepgram options
            options = PrerecordedOptions(
                model="nova-3",
                language="en",
                summarize="v2",
                topics=True,
                intents=True,
                detect_entities=True,
                smart_format=True,
                sentiment=True,
            )

            # Transcribe file
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify(response.to_dict())
        
        return jsonify({'error': 'Invalid file format'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Use Render's PORT env variable
    app.run(host='0.0.0.0', port=port, debug=False)
