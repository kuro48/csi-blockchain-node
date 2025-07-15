FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# アプリケーションコードのコピー
COPY main.py .
COPY worker/ ./worker/
COPY config/ ./config/

# 必要なディレクトリの作成
RUN mkdir -p /app/data/logs /app/data/analysis /app/data/temp

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# デフォルトコマンド
CMD ["python", "main.py", "--mode", "analysis-monitor"] 