# CSI Blockchain Node 統合ガイド

このガイドでは、CSI Blockchain Node が分析サーバーとエッジデバイスとどのように統合されるかを説明します。

## システム構成

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  CSI Edge       │    │  Analysis        │    │  Blockchain     │
│  Device         │───▶│  Server          │───▶│  Node           │
│                 │    │                  │    │                 │
│ - CSI収集       │    │ - 呼吸解析       │    │ - IPFS保存      │
│ - データ送信    │    │ - 結果保存       │    │ - ブロックチェーン記録
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  IPFS Node      │
                       │                 │
                       │ - データ保存    │
                       │ - ハッシュ管理  │
                       └─────────────────┘
```

## データフロー

### 1. エッジデバイス → 分析サーバー

1. **CSIデータ収集**: エッジデバイスがCSIデータを収集
2. **データ送信**: HTTP API経由で分析サーバーに送信
3. **解析実行**: 分析サーバーが呼吸解析を実行
4. **結果保存**: 解析結果をデータベースに保存

### 2. 分析サーバー → ブロックチェーンノード

1. **結果監視**: ブロックチェーンノードが分析サーバーを定期的に監視
2. **結果取得**: HTTP API経由で解析結果を取得
3. **IPFS保存**: 解析結果をIPFSに保存
4. **ブロックチェーン記録**: メタデータとIPFSハッシュをブロックチェーンに記録

## 設定手順

### 1. 分析サーバーの設定

```bash
# 分析サーバーディレクトリに移動
cd ../csi-analysis-server

# 設定ファイルの準備
cp config/config.json.example config/config.json

# 設定を編集
# - IPFS設定
# - APIキー設定
# - データベース設定
```

### 2. エッジデバイスの設定

```bash
# エッジデバイスディレクトリに移動
cd ../csi-edge-device

# 設定ファイルの準備
cp config/device_config.json.example config/device_config.json

# 設定を編集
# - 分析サーバーのURL
# - APIキー
# - デバイスID
```

### 3. ブロックチェーンノードの設定

```bash
# ブロックチェーンノードディレクトリに移動
cd ../csi-blockchain-node

# 設定ファイルの準備
cp config/blockchain_config.json.example config/blockchain_config.json

# 設定を編集
# - IPFS設定（Docker環境用）
# - イーサリアム設定
# - 分析サーバー設定
```

## Docker Compose での統合実行

### 1. 統合docker-compose.ymlの作成

```yaml
version: '3.8'

services:
  # IPFS ノード
  ipfs:
    image: ipfs/kubo:latest
    container_name: csi-ipfs
    ports:
      - "4001:4001"
      - "5001:5001"
      - "8080:8080"
    volumes:
      - ipfs_data:/data/ipfs
    environment:
      - IPFS_PROFILE=server
    command: daemon --migrate=true --agent-version-suffix=docker
    networks:
      - csi-network

  # 分析サーバー
  analysis-server:
    build: ../csi-analysis-server
    container_name: csi-analysis-server
    ports:
      - "8000:8000"
    volumes:
      - analysis_data:/app/data
    environment:
      - IPFS_HOST=ipfs
      - IPFS_PORT=5001
      - API_KEY=your-secret-api-key
    depends_on:
      - ipfs
    networks:
      - csi-network

  # ブロックチェーンノード
  blockchain-node:
    build: .
    container_name: csi-blockchain-node
    volumes:
      - blockchain_data:/app/data
    environment:
      - IPFS_HOST=ipfs
      - IPFS_PORT=5001
      - ANALYSIS_SERVER_URL=http://analysis-server:8000
      - API_KEY=your-secret-api-key
    depends_on:
      - ipfs
      - analysis-server
    networks:
      - csi-network
    restart: unless-stopped

volumes:
  ipfs_data:
  analysis_data:
  blockchain_data:

networks:
  csi-network:
    driver: bridge
```

### 2. 統合システムの起動

```bash
# 全システムの起動
docker-compose up -d

# ログの確認
docker-compose logs -f

# 個別サービスのログ確認
docker-compose logs -f analysis-server
docker-compose logs -f blockchain-node
```

## API エンドポイント

### 分析サーバー API

- `POST /breathing-analysis/analyze` - 呼吸解析の実行
- `POST /breathing-analysis/upload-csi` - CSIファイルのアップロード
- `GET /breathing-analysis/results/{device_id}` - 解析結果の取得
- `GET /breathing-analysis/results/{device_id}/latest` - 最新結果の取得
- `GET /breathing-analysis/health` - ヘルスチェック

### ブロックチェーンノード API

- `GET /blockchain/status` - ブロックチェーン状態の取得
- `GET /blockchain/data/{index}` - 特定のデータの取得
- `GET /blockchain/data` - 全データの取得

## 監視とログ

### ログファイルの場所

- **分析サーバー**: `/app/logs/` (コンテナ内)
- **ブロックチェーンノード**: `/app/data/logs/` (コンテナ内)
- **IPFS**: 標準出力

### 監視コマンド

```bash
# 全サービスの状態確認
docker-compose ps

# リアルタイムログ監視
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f analysis-server
docker-compose logs -f blockchain-node

# リソース使用量確認
docker stats
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. 分析サーバーに接続できない

```bash
# 分析サーバーの状態確認
curl http://localhost:8000/breathing-analysis/health

# ログの確認
docker-compose logs analysis-server
```

#### 2. IPFSに接続できない

```bash
# IPFSノードの状態確認
curl http://localhost:5001/api/v0/id

# ログの確認
docker-compose logs ipfs
```

#### 3. ブロックチェーンノードが起動しない

```bash
# 設定ファイルの確認
docker-compose exec blockchain-node cat config/blockchain_config.json

# 接続テスト
docker-compose exec blockchain-node python main.py --mode test
```

#### 4. データが流れない

```bash
# 全サービスの状態確認
docker-compose ps

# ネットワーク接続確認
docker-compose exec blockchain-node ping analysis-server
docker-compose exec blockchain-node ping ipfs

# 分析サーバーのAPI確認
curl -H "X-API-Key: your-api-key" http://localhost:8000/breathing-analysis/health
```

## パフォーマンス最適化

### 1. リソース制限の設定

```yaml
services:
  analysis-server:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  blockchain-node:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### 2. 監視間隔の調整

```json
{
  "analysis_server": {
    "polling_interval": 30,  // 30秒間隔
    "batch_size": 20         // 20件ずつ処理
  }
}
```

### 3. ログローテーション

```yaml
services:
  analysis-server:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  blockchain-node:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## セキュリティ考慮事項

### 1. APIキーの管理

- 環境変数で管理
- 定期的な更新
- 最小権限の原則

### 2. ネットワークセキュリティ

- 内部ネットワークの使用
- 不要なポートの閉鎖
- ファイアウォールの設定

### 3. データ暗号化

- 転送時の暗号化（HTTPS）
- 保存時の暗号化
- 秘密鍵の安全な管理

## 拡張性

### 1. スケールアウト

- 複数の分析サーバーインスタンス
- ロードバランサーの導入
- データベースのクラスタリング

### 2. 高可用性

- サービスレプリケーション
- 自動フェイルオーバー
- バックアップ戦略

### 3. 監視とアラート

- Prometheus + Grafana
- アラート通知
- メトリクス収集 