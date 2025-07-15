import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AnalysisServerClient:
    """分析サーバーとの通信を行うクライアント"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        分析サーバークライアントの初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.base_url = config['analysis_server']['base_url']
        self.api_key = config['analysis_server']['api_key']
        self.endpoints = config['analysis_server']['endpoints']
        self.session = None
        
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession(
            headers={
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
            
    async def health_check(self) -> bool:
        """
        分析サーバーのヘルスチェック
        
        Returns:
            サーバーが正常かどうか
        """
        try:
            url = f"{self.base_url}{self.endpoints['health']}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"分析サーバーのヘルスチェック成功: {data}")
                    return True
                else:
                    logger.error(f"分析サーバーのヘルスチェック失敗: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"分析サーバーのヘルスチェック中にエラー: {e}")
            return False
            
    async def get_analysis_results(
        self, 
        device_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        分析結果の取得
        
        Args:
            device_id: デバイスID
            start_time: 開始時刻（UNIXタイムスタンプ）
            end_time: 終了時刻（UNIXタイムスタンプ）
            limit: 取得件数制限
            
        Returns:
            分析結果のリスト
        """
        try:
            url = f"{self.base_url}{self.endpoints['results']}/{device_id}"
            params = {'limit': limit}
            
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
                
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"分析結果を取得しました: {device_id}, 件数: {data.get('count', 0)}")
                    return data.get('results', [])
                else:
                    logger.error(f"分析結果の取得に失敗: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"分析結果取得中にエラー: {e}")
            return []
            
    async def get_latest_analysis_result(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        最新の分析結果の取得
        
        Args:
            device_id: デバイスID
            
        Returns:
            最新の分析結果
        """
        try:
            url = f"{self.base_url}{self.endpoints['latest'].format(device_id=device_id)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"最新の分析結果を取得しました: {device_id}")
                    return data
                else:
                    logger.error(f"最新の分析結果の取得に失敗: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"最新の分析結果取得中にエラー: {e}")
            return None
            
    async def get_all_devices_results(self, limit_per_device: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        全デバイスの分析結果を取得
        
        Args:
            limit_per_device: デバイスごとの取得件数
            
        Returns:
            デバイスIDをキーとした分析結果の辞書
        """
        try:
            # 全デバイスの結果を取得（実際の実装ではデバイスリストの取得が必要）
            # ここでは例として固定のデバイスIDを使用
            device_ids = ['edge-device-001', 'edge-device-002']  # 設定から取得するように変更
            
            all_results = {}
            for device_id in device_ids:
                results = await self.get_analysis_results(
                    device_id=device_id,
                    limit=limit_per_device
                )
                if results:
                    all_results[device_id] = results
                    
            logger.info(f"全デバイスの分析結果を取得しました: {len(all_results)} デバイス")
            return all_results
            
        except Exception as e:
            logger.error(f"全デバイスの分析結果取得中にエラー: {e}")
            return {} 