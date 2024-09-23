FROM python:3.10-slim

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y \
    gdal-bin \
    python3-gdal \
    build-essential \
    libgdal-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを作成
WORKDIR /app

# Pythonの仮想環境を作成
RUN python -m venv /venv

# 仮想環境を有効化
ENV PATH="/venv/bin:$PATH"

# 必要なPythonパッケージをインストール
RUN pip install --upgrade pip \
    && pip install \
    langchain \
    langchain-openai \
    'pydeck==0.8.0' \
    'plateaukit[all]' \
    osmnx \
    geopandas \
    pandas \
    python-dotenv \
    networkx \
    scikit-learn \
    openai \
    shapely \
    flask \
    flask-cors \
    vertexai

# Node.jsの最新バージョンをインストール
RUN npm install -g npm@latest

# package.jsonとpackage-lock.jsonをコピーして依存関係をインストール
COPY package.json package-lock.json ./
RUN npm install

# 作業ディレクトリ内のファイルをコピー
COPY . .

# ポートの公開
EXPOSE 5050 80

# FlaskとNode.jsを同時に起動するスクリプトを作成
COPY start.sh /start.sh
RUN chmod +x /start.sh

# デフォルトの起動コマンド
CMD ["/start.sh"]
