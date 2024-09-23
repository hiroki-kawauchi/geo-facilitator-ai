
def transcribe_audio(client, audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        response = client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file,
            response_format='text',
            language='ja',
            prompt='サンシャインシティ, サンシャイン通り, 東京駅'
        )
    return response