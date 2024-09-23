import dotenv from 'dotenv';
import fs from 'node:fs';
import OpenAI from 'openai';
import os from 'os';
import path from 'path';

// OpenAIの設定を行う
//dotenvで環境変数を読み込む
dotenv.config();
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const openai = new OpenAI({
  apiKey:  OPENAI_API_KEY,
});

// Macのダウンロードディレクトリのパスを構築
const audioFilePath = path.join(os.homedir(), 'Downloads', 'recording.mp3');

function deleteFile(filePath) {
    fs.unlink(filePath, (err) => {
        if (err) {
            console.error('Error deleting the file:', err);
        } else {
            console.log('File deleted successfully:', filePath);
        }
    });
}

async function main() {
    // Whisperモデルを使用してテキスト変換リクエストを送信
    const response = await openai.audio.transcriptions.create({
        model: "whisper-1",
        file: fs.createReadStream(audioFilePath),
        language: "ja",
        prompt: 'サンシャインシティ, サンシャイン通り, 東京駅'
    });

    // 変換されたテキストを出力
    console.log(response);

    // オーディオファイルを削除
    deleteFile(audioFilePath);
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});