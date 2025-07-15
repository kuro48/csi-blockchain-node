#!/usr/bin/env python3
"""
PC2ブロックチェーンノードメインスクリプト
呼吸解析データをIPFSとブロックチェーンに保存するノード
"""

import json
import os
import sys
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Any
import asyncio
import schedule

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from worker.blockchain_manager import BlockchainManager

class BlockchainNodeManager:
    """ブロックチェーンノード管理クラス"""
    
    def __init__(self, config_path: str):
        """
        ブロックチェーンノードマネージャーの初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        
        # ブロックチェーンマネージャーの初期化
        self.blockchain_manager = BlockchainManager(self.config)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            sys.exit(1)
            
    def _setup_logging(self):
        """ロギングの設定"""
        log_dir = self.config['storage']['logs_dir']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'blockchain_node_{timestamp}.log')
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format=self.config['logging']['format'],
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Blockchain Node Manager initialized")
        
    def _setup_directories(self):
        """必要なディレクトリの作成"""
        storage_config = self.config['storage']
        directories = [
            storage_config['base_dir'],
            storage_config['data_dir'],
            storage_config['logs_dir'],
            storage_config['temp_dir']
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"ディレクトリを作成しました: {directory}")
                
    def process_analysis_file(self, file_path: str) -> bool:
        """
        解析ファイルの処理
        
        Args:
            file_path: 解析ファイルのパス
            
        Returns:
            処理成功フラグ
        """
        try:
            self.logger.info(f"解析ファイルの処理を開始: {file_path}")
            
            # ファイルの読み込み
            with open(file_path, 'r') as f:
                analysis_data = json.load(f)
                
            # ブロックチェーンへの保存
            result = self.blockchain_manager.process_breathing_analysis(analysis_data)
            
            self.logger.info(f"解析ファイルの処理が完了: {result['transaction_hash']}")
            
            # 処理済みファイルの移動
            processed_dir = os.path.join(self.config['storage']['data_dir'], 'processed')
            os.makedirs(processed_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"processed_{timestamp}_{os.path.basename(file_path)}"
            new_path = os.path.join(processed_dir, new_filename)
            
            os.rename(file_path, new_path)
            self.logger.info(f"処理済みファイルを移動しました: {new_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"解析ファイル処理中にエラーが発生: {e}")
            return False
            
    def monitor_data_directory(self):
        """データディレクトリの監視"""
        try:
            data_dir = self.config['storage']['data_dir']
            pending_dir = os.path.join(data_dir, 'pending')
            
            if not os.path.exists(pending_dir):
                os.makedirs(pending_dir)
                
            # 待機中のファイルを検索
            json_files = [f for f in os.listdir(pending_dir) if f.endswith('.json')]
            
            for filename in json_files:
                file_path = os.path.join(pending_dir, filename)
                
                try:
                    # ファイルの処理
                    if self.process_analysis_file(file_path):
                        self.logger.info(f"ファイルの処理が成功しました: {filename}")
                    else:
                        self.logger.error(f"ファイルの処理に失敗しました: {filename}")
                        
                except Exception as e:
                    self.logger.error(f"ファイル処理中にエラーが発生 {filename}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"データディレクトリ監視中にエラーが発生: {e}")
            
    def get_blockchain_status(self) -> Dict[str, Any]:
        """
        ブロックチェーンの状態取得
        
        Returns:
            ブロックチェーン状態
        """
        try:
            count = self.blockchain_manager.get_breathing_data_count()
            
            status = {
                'total_records': count,
                'last_updated': datetime.now().isoformat(),
                'node_id': self.config['node']['id'],
                'network': self.config['ethereum']['network']
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"ブロックチェーン状態取得中にエラーが発生: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
            
    def run_scheduled_tasks(self):
        """スケジュールされたタスクの実行"""
        try:
            # データディレクトリ監視のスケジュール
            schedule.every(30).seconds.do(self.monitor_data_directory)
            
            # ブロックチェーン状態確認のスケジュール
            schedule.every(5).minutes.do(self.get_blockchain_status)
            
            self.logger.info("スケジュールされたタスクを開始しました")
            
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("スケジュールされたタスクを停止しました")
        except Exception as e:
            self.logger.error(f"スケジュールタスク実行中にエラーが発生: {e}")
            
    def test_connection(self) -> bool:
        """接続テスト"""
        try:
            # IPFS接続テスト
            self.blockchain_manager.ipfs_client.id()
            self.logger.info("IPFS接続テストが成功しました")
            
            # Ethereum接続テスト
            count = self.blockchain_manager.get_breathing_data_count()
            self.logger.info(f"Ethereum接続テストが成功しました: データ数 {count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"接続テストに失敗: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="ブロックチェーンノードメインスクリプト")
    parser.add_argument("--config", type=str, default="config/blockchain_config.json",
                      help="設定ファイルのパス")
    parser.add_argument("--mode", type=str, choices=["monitor", "process", "test"],
                      default="monitor", help="実行モード")
    parser.add_argument("--file", type=str, help="処理対象のファイル（processモード用）")
    
    args = parser.parse_args()
    
    # ブロックチェーンノードマネージャーの初期化
    manager = BlockchainNodeManager(args.config)
    
    # 接続テスト
    if not manager.test_connection():
        manager.logger.error("接続テストに失敗しました。設定を確認してください。")
        sys.exit(1)
    
    # モードに応じた実行
    if args.mode == "monitor":
        manager.run_scheduled_tasks()
    elif args.mode == "process":
        if not args.file:
            print("エラー: processモードでは--fileが必要です")
            sys.exit(1)
        success = manager.process_analysis_file(args.file)
        sys.exit(0 if success else 1)
    elif args.mode == "test":
        status = manager.get_blockchain_status()
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main() 