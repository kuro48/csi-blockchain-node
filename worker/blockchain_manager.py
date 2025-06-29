import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import ipfshttpclient
from web3 import Web3
from web3.exceptions import ContractLogicError, ValidationError
import asyncio

logger = logging.getLogger(__name__)

class BlockchainManager:
    """ブロックチェーン管理クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        ブロックチェーンマネージャーの初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self._setup_logging()
        self._setup_ipfs()
        self._setup_ethereum()
        
    def _setup_logging(self):
        """ロギングの設定"""
        log_dir = self.config.get('log_dir', '/app/logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'blockchain_manager_{timestamp}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def _setup_ipfs(self):
        """IPFSクライアントの設定"""
        try:
            ipfs_api_url = self.config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
            self.ipfs_client = ipfshttpclient.connect(ipfs_api_url)
            logger.info(f"IPFSクライアントを初期化しました: {ipfs_api_url}")
        except Exception as e:
            logger.error(f"IPFSクライアントの初期化に失敗: {e}")
            raise
            
    def _setup_ethereum(self):
        """Ethereumクライアントの設定"""
        try:
            ethereum_config = self.config.get('ethereum', {})
            rpc_url = ethereum_config.get('rpc_url', 'http://localhost:8545')
            contract_address = ethereum_config.get('contract_address')
            private_key = ethereum_config.get('private_key')
            
            if not all([contract_address, private_key]):
                raise ValueError("コントラクトアドレスと秘密鍵が必要です")
                
            # Web3の初期化
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                raise ConnectionError("Ethereumノードに接続できません")
                
            # コントラクトの設定
            self.contract_address = contract_address
            self.private_key = private_key
            
            # コントラクトのABI（簡略化版）
            self.contract_abi = [
                {
                    "inputs": [
                        {"internalType": "string", "name": "ipfsHash", "type": "string"},
                        {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                        {"internalType": "string", "name": "deviceId", "type": "string"}
                    ],
                    "name": "storeBreathingData",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "", "type": "uint256"}
                    ],
                    "name": "breathingData",
                    "outputs": [
                        {"internalType": "string", "name": "ipfsHash", "type": "string"},
                        {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                        {"internalType": "string", "name": "deviceId", "type": "string"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "getBreathingDataCount",
                    "outputs": [
                        {"internalType": "uint256", "name": "", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # コントラクトのインスタンス化
            self.contract = self.w3.eth.contract(
                address=contract_address,
                abi=self.contract_abi
            )
            
            # アカウントの設定
            self.account = self.w3.eth.account.from_key(private_key)
            self.w3.eth.default_account = self.account.address
            
            logger.info(f"Ethereumクライアントを初期化しました: {rpc_url}")
            logger.info(f"コントラクトアドレス: {contract_address}")
            logger.info(f"アカウントアドレス: {self.account.address}")
            
        except Exception as e:
            logger.error(f"Ethereumクライアントの初期化に失敗: {e}")
            raise
            
    def store_to_ipfs(self, data: Dict[str, Any]) -> str:
        """
        データをIPFSに保存
        
        Args:
            data: 保存するデータ
            
        Returns:
            IPFSハッシュ
        """
        try:
            # JSONデータをIPFSに追加
            result = self.ipfs_client.add_json(data)
            logger.info(f"データをIPFSに保存しました: {result}")
            return result
        except Exception as e:
            logger.error(f"IPFSへの保存に失敗: {e}")
            raise
            
    def store_to_blockchain(self, ipfs_hash: str, timestamp: int, device_id: str) -> Dict[str, Any]:
        """
        IPFSハッシュをブロックチェーンに保存
        
        Args:
            ipfs_hash: IPFSハッシュ
            timestamp: タイムスタンプ
            device_id: デバイスID
            
        Returns:
            トランザクション結果
        """
        try:
            # トランザクションの構築
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price
            
            # トランザクションの作成
            transaction = self.contract.functions.storeBreathingData(
                ipfs_hash,
                timestamp,
                device_id
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': gas_price
            })
            
            # トランザクションの署名
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                self.private_key
            )
            
            # トランザクションの送信
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            result = {
                'transaction_hash': receipt['transactionHash'].hex(),
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'status': receipt['status']
            }
            
            logger.info(f"ブロックチェーンへの保存が成功しました: {result['transaction_hash']}")
            return result
            
        except Exception as e:
            logger.error(f"ブロックチェーンへの保存に失敗: {e}")
            raise
            
    def get_breathing_data_count(self) -> int:
        """
        保存されている呼吸データの数を取得
        
        Returns:
            データ数
        """
        try:
            count = self.contract.functions.getBreathingDataCount().call()
            return count
        except Exception as e:
            logger.error(f"データ数の取得に失敗: {e}")
            return 0
            
    def get_breathing_data(self, index: int) -> Optional[Dict[str, Any]]:
        """
        指定されたインデックスの呼吸データを取得
        
        Args:
            index: データインデックス
            
        Returns:
            呼吸データ（見つからない場合はNone）
        """
        try:
            data = self.contract.functions.breathingData(index).call()
            return {
                'ipfs_hash': data[0],
                'timestamp': data[1],
                'device_id': data[2]
            }
        except Exception as e:
            logger.error(f"呼吸データの取得に失敗: {e}")
            return None
            
    def get_data_from_ipfs(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """
        IPFSからデータを取得
        
        Args:
            ipfs_hash: IPFSハッシュ
            
        Returns:
            データ（見つからない場合はNone）
        """
        try:
            data = self.ipfs_client.get_json(ipfs_hash)
            return data
        except Exception as e:
            logger.error(f"IPFSからのデータ取得に失敗: {e}")
            return None
            
    def process_breathing_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        呼吸解析データの処理とブロックチェーンへの保存
        
        Args:
            analysis_data: 呼吸解析データ
            
        Returns:
            処理結果
        """
        try:
            logger.info(f"呼吸解析データの処理を開始: デバイスID {analysis_data.get('metadata', {}).get('device_id', 'unknown')}")
            
            # タイムスタンプの追加
            analysis_data['blockchain_timestamp'] = int(datetime.now().timestamp())
            
            # IPFSに保存
            ipfs_hash = self.store_to_ipfs(analysis_data)
            
            # ブロックチェーンに保存
            receipt = self.store_to_blockchain(
                ipfs_hash,
                analysis_data['blockchain_timestamp'],
                analysis_data['metadata']['device_id']
            )
            
            result = {
                'ipfs_hash': ipfs_hash,
                'transaction_hash': receipt['transaction_hash'],
                'block_number': receipt['block_number'],
                'timestamp': analysis_data['blockchain_timestamp']
            }
            
            logger.info(f"呼吸解析データの処理が完了しました")
            return result
            
        except Exception as e:
            logger.error(f"呼吸解析データ処理中にエラーが発生: {e}")
            raise
            
    def get_all_breathing_data(self) -> List[Dict[str, Any]]:
        """
        すべての呼吸データを取得
        
        Returns:
            呼吸データ一覧
        """
        try:
            count = self.get_breathing_data_count()
            data_list = []
            
            for i in range(count):
                data = self.get_breathing_data(i)
                if data:
                    # IPFSから詳細データを取得
                    ipfs_data = self.get_data_from_ipfs(data['ipfs_hash'])
                    if ipfs_data:
                        data['analysis_data'] = ipfs_data
                    data_list.append(data)
                    
            return data_list
            
        except Exception as e:
            logger.error(f"全呼吸データの取得に失敗: {e}")
            return [] 