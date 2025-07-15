# CSI Blockchain Node

CSI解析結果をIPFSとイーサリアムブロックチェーンに保存するノードです。

## 概要

このノードは、分析サーバーから呼吸解析結果を取得し、IPFSにデータを保存し、イーサリアムブロックチェーンにメタデータを記録します。分析サーバーとIPFSノードと連携して動作します。

## 機能

- **分析サーバー連携**: 分析サーバーから解析結果を自動取得
- **IPFS保存**: 解析結果ファイルをIPFSに保存
- **ブロックチェーン記録**: イーサリアムブロックチェーンにメタデータを記録
- **データ検証**: 保存されたデータの整合性確認
- **自動監視**: 分析サーバーの定期的な監視と処理
- **非同期処理**: 効率的な非同期データ処理

## セットアップ

### 必要条件

- Python 3.11以上
- Docker と Docker Compose
- イーサリアムノード（ローカルまたはリモート）
- 分析サーバーとIPFSノード（Dockerコンテナ）

### インストール

#### Dockerを使用した方法（推奨）

```bash
# 設定ファイルの準備
cp config/blockchain_config.json.example config/blockchain_config.json
# 設定ファイルを編集して、イーサリアム設定を追加

# Docker Composeで起動
docker-compose up -d
```

#### 手動インストール

```bash
# Python依存関係のインストール
pip install -r requirements.txt

# 設定ファイルの準備
cp config/blockchain_config.json.example config/blockchain_config.json
```

### 設定

`config/blockchain_config.json`を編集：

```json
{
  "ipfs": {
    "api_url": "/ip4/ipfs/tcp/5001"
  },
  "ethereum": {
    "rpc_url": "http://localhost:8545",
    "contract_address": "0x...",
    "private_key": "0x..."
  },
  "analysis_server": {
    "base_url": "http://analysis-server:8000",
    "api_key": "your-api-key-here",
    "polling_interval": 60,
    "batch_size": 10
  },
  "monitoring": {
    "data_dir": "/app/data/analysis",
    "check_interval": 60
  }
}
```

## アーキテクチャ

```
CSI Blockchain Node
├── main.py                 # メインスクリプト
├── worker/
│   ├── blockchain_manager.py  # ブロックチェーン管理
│   └── http_client.py         # 分析サーバー通信
├── config/                 # 設定ファイル
├── Dockerfile              # Docker設定
├── docker-compose.yml      # コンテナ構成
└── requirements.txt        # 依存関係
```

## データフロー

1. **分析サーバー監視**: 分析サーバーから解析結果を定期的に取得
2. **IPFS保存**: 解析結果ファイルをIPFSにアップロード
3. **ハッシュ取得**: IPFSからコンテンツハッシュを取得
4. **ブロックチェーン記録**: メタデータとIPFSハッシュをブロックチェーンに記録
5. **検証**: 保存されたデータの整合性を確認

## 使用方法

### 分析サーバー監視モード（推奨）

```bash
# Docker Composeで起動
docker-compose up -d

# または手動で実行
python main.py --mode analysis-monitor
```

### 分析結果一括処理

```bash
python main.py --mode analysis-process --limit 50
```

### 従来の監視モード

```bash
python main.py --mode monitor
```

### 単一ファイル処理

```bash
python main.py --mode process --file /path/to/analysis.json
```

### 接続テスト

```bash
python main.py --mode test
```

## 設定詳細

### IPFS設定

```python
# IPFS API URL（Docker環境）
IPFS_API_URL = "/ip4/ipfs/tcp/5001"

# IPFS設定
ipfs_config = {
    "api_url": IPFS_API_URL,
    "timeout": 30
}
```

### イーサリアム設定

```python
# イーサリアム設定
ethereum_config = {
    "rpc_url": "http://localhost:8545",
    "contract_address": "0x...",
    "private_key": "0x...",
    "gas_limit": 3000000,
    "gas_price": 20000000000
}
```

## スマートコントラクト

### データ保存コントラクト

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CSIDataStorage {
    struct AnalysisData {
        string deviceId;
        uint256 timestamp;
        uint256 breathingRate;
        string ipfsHash;
        string location;
    }
    
    mapping(bytes32 => AnalysisData) public dataRecords;
    
    event DataStored(bytes32 indexed dataId, string deviceId, uint256 timestamp);
    
    function storeData(
        string memory deviceId,
        uint256 timestamp,
        uint256 breathingRate,
        string memory ipfsHash,
        string memory location
    ) public {
        bytes32 dataId = keccak256(abi.encodePacked(deviceId, timestamp));
        
        dataRecords[dataId] = AnalysisData({
            deviceId: deviceId,
            timestamp: timestamp,
            breathingRate: breathingRate,
            ipfsHash: ipfsHash,
            location: location
        });
        
        emit DataStored(dataId, deviceId, timestamp);
    }
}
```

## トラブルシューティング

### よくある問題

- **IPFS接続エラー**: IPFSコンテナの起動確認
- **分析サーバー接続エラー**: 分析サーバーコンテナの起動確認
- **ブロックチェーンエラー**: イーサリアムノードの接続確認
- **ガス代不足**: イーサリアムアカウントの残高確認
- **Docker接続エラー**: ネットワーク設定の確認

### ログ確認

```bash
tail -f logs/blockchain_*.log
```

## セキュリティ

- **秘密鍵管理**: 環境変数または安全なキーストアで管理
- **データ検証**: IPFSハッシュによるデータ整合性確認
- **アクセス制御**: 適切な権限設定

## ライセンス

このプロジェクトは研究目的で開発されています。 