#!/bin/bash

# CSI Blockchain Node 起動スクリプト

set -e

echo "CSI Blockchain Node を起動しています..."

# 設定ファイルの確認
if [ ! -f "config/blockchain_config.json" ]; then
    echo "設定ファイルが見つかりません。"
    echo "config/blockchain_config.json.example をコピーして設定してください。"
    exit 1
fi

# 必要なディレクトリの作成
mkdir -p data/logs data/analysis data/temp

# Python依存関係の確認
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストールしています..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 環境変数の設定
export PYTHONPATH=$(pwd)
export PYTHONUNBUFFERED=1

# 実行モードの確認
MODE=${1:-analysis-monitor}

echo "実行モード: $MODE"

# メインスクリプトの実行
case $MODE in
    "analysis-monitor")
        echo "分析サーバー監視モードで起動します..."
        python main.py --mode analysis-monitor
        ;;
    "analysis-process")
        echo "分析結果一括処理モードで起動します..."
        python main.py --mode analysis-process --limit 50
        ;;
    "monitor")
        echo "従来の監視モードで起動します..."
        python main.py --mode monitor
        ;;
    "test")
        echo "接続テストを実行します..."
        python main.py --mode test
        ;;
    *)
        echo "無効なモードです: $MODE"
        echo "使用可能なモード: analysis-monitor, analysis-process, monitor, test"
        exit 1
        ;;
esac 