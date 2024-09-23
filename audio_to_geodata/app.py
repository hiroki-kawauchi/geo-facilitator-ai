import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # すべてのオリジンからのアクセスを許可

@app.route('/backend-test')
def index():
   return '<h1>Backend</h1>'

# ファイルの保存先ディレクトリ
UPLOAD_FOLDER = '../audio_to_geodata/data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# '/upload' エンドポイント - 音声ファイルを保存する
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # ファイルを保存
        file_path = os.path.join(UPLOAD_FOLDER, 'recording.mp3')
        file.save(file_path)

        return jsonify({'message': 'File uploaded successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Pythonスクリプトを実行するエンドポイント
@app.route('/run-python', methods=['POST'])
def run_python():
    try:
        # クエリをPOSTリクエストから取得
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({'error': 'Query is missing'}), 400

        # コマンドライン引数としてmain.pyにクエリを渡して実行
        process = subprocess.Popen(['python3', 'main.py', query], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return jsonify({'error': stderr.decode('utf-8')}), 500

        return jsonify({'result': stdout.decode('utf-8')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Pythonスクリプトを実行するエンドポイント
@app.route('/run-python-string-query', methods=['POST'])
def run_python_string_query():
    try:
        # クエリをPOSTリクエストから取得
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({'error': 'Query is missing'}), 400

        # コマンドライン引数としてmain.pyにクエリを渡して実行
        process = subprocess.Popen(['python3', 'main_string_query.py', query], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return jsonify({'error': stderr.decode('utf-8')}), 500

        return jsonify({'result': stdout.decode('utf-8')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
