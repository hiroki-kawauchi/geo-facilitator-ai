# deckgl-env
### 環境構築
1. docker-compose
    ```bash
    $ docker-compose up -d
    ```
2. 以下のURLにアクセス：
* http://localhost/mapengine-survey/step3/deckgl-linelayer/
    * vite.config.jsにてアドレスを定義

### Flask APIをバックグラウンドで起動

- start.shが失敗するため、以下の方法で手動でflaskを起動してください。
- Google Cloudのサービスアカウントキーのバスを環境変数 GOOGLE_APPLICATION_CREDENTIALS に設定してください。

```
cd audio_to_geodata
pip install google-cloud-speech google-cloud-aiplatform
export GOOGLE_APPLICATION_CREDENTIALS="./service_account_file/service-account-file.json"
flask run --host=0.0.0.0 --port=5050 &
```

- 以下のURLからmain_string_query.pyを起動することができます。

```
curl -X POST http://localhost:5050/run-python-string-query \
-H "Content-Type: application/json" \
-d '{"query": "予定地の洪水時想定最大浸水深を表示してください"}'
```

- また、下記のコマンドでpythonを直接実行可能です。

```
python main_string_query.py "add two numbers 3 and 5"
```

- 音声文字起こしは下記のコマンドでテスト可能です。
  - 現状GCPで動作しないためフロントから音声入力部分を削除しています。

```
python main.py ./data/large_building.m4a
```
