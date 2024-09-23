#!/bin/bash

# Flask APIをバックグラウンドで起動
flask run --host=0.0.0.0 --port=5050 &

# React (Node.js) サーバーを起動
npm run dev
