# CSI Blockchain Node

CSI解析結果をIPFSとイーサリアムブロックチェーンに保存するノードです。

## 概要

このノードは、解析サーバーから送信された呼吸解析結果を受け取り、IPFSにデータを保存し、イーサリアムブロックチェーンにメタデータを記録します。

## 機能

- **データ監視**: 解析結果ディレクトリの監視
- **IPFS保存**: 解析結果ファイルをIPFSに保存
- **ブロックチェーン記録**: イーサリアムブロックチェーンにメタデータを記録
- **データ検証**: 保存されたデータの整合性確認
- **スケジュール実行**: 定期的なデータ処理と監視

## セットアップ

### 必要条件

- Python 3.8以上
- IPFSデーモン
- イーサリアムノード（ローカルまたはリモート）
- Web3.py

### インストール

```bash
# IPFSのインストール
wget https://dist.ipfs.io/go-ipfs/v0.12.0/go-ipfs_v0.12.0_linux-amd64.tar.gz
tar -xvzf go-ipfs_v0.12.0_linux-amd64.tar.gz
cd go-ipfs
sudo ./install.sh
ipfs init
ipfs daemon &

# Python依存関係のインストール
pip install -r requirements.txt
```

### 設定

`config/blockchain_config.json`を編集：

```json
{
  "ipfs": {
    "api_url": "/ip4/127.0.0.1/tcp/5001"
  },
  "ethereum": {
    "rpc_url": "http://localhost:8545",
    "contract_address": "0x...",
    "private_key": "0x..."
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
│   └── blockchain_manager.py  # ブロックチェーン管理
├── config/                 # 設定ファイル
└── requirements.txt        # 依存関係
```

## データフロー

1. **データ監視**: 解析結果ディレクトリを監視
2. **IPFS保存**: 解析結果ファイルをIPFSにアップロード
3. **ハッシュ取得**: IPFSからコンテンツハッシュを取得
4. **ブロックチェーン記録**: メタデータとIPFSハッシュをブロックチェーンに記録
5. **検証**: 保存されたデータの整合性を確認

## 使用方法

### 監視モード（推奨）

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
# IPFS API URL
IPFS_API_URL = "/ip4/127.0.0.1/tcp/5001"

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

- **IPFS接続エラー**: IPFSデーモンの起動確認
- **ブロックチェーンエラー**: イーサリアムノードの接続確認
- **ガス代不足**: イーサリアムアカウントの残高確認

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