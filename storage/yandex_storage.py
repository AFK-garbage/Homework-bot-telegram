# storage/yandex_storage.py
import os
import asyncio
import aiofiles
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class YandexCloudStorage:
    """Реальное хранилище Яндекс Облака (S3-совместимое)"""
    
    def __init__(self, access_key: str, secret_key: str, bucket: str, region: str = "ru-central1"):

        self.provider_type = 'yandex'
    
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.region = region
    
        import boto3
        self.s3 = boto3.client(
            's3',
            endpoint_url=f'https://storage.yandexcloud.net',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
    )
    
        try:
            self.s3.head_bucket(Bucket=bucket)
            logger.info(f"✅ Подключение к Yandex Cloud bucket '{bucket}' успешно")
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к bucket '{bucket}': {e}")
            raise

    async def save(self, file_content: bytes, filename: str, metadata: dict = None) -> Dict[str, Any]:
        """
        Сохраняет файл в Яндекс Облако
        """
        try:
            # Генерируем уникальное имя файла
            file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{asyncio.get_event_loop().time()}.bin"
            
            # Добавляем метаданные
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}
            
            # Сохраняем файл асинхронно (в отдельном потоке)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.put_object(
                    Bucket=self.bucket,
                    Key=file_id,
                    Body=file_content,
                    **extra_args
                )
            )
            
            # Формируем результат
            file_info = {
                'id': file_id,
                'original_name': filename,
                'url': f"https://storage.yandexcloud.net/{self.bucket}/{file_id}",
                'size': len(file_content),
                'saved_at': datetime.now().isoformat(),
                'provider': 'yandex'
            }
            
            logger.info(f"✅ Файл сохранен в Yandex Cloud: {file_id} ({len(file_content)} байт)")
            return file_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в Yandex Cloud: {e}")
            raise
    
    async def get(self, file_id: str) -> bytes:
        """
        Скачивает файл из Яндекс Облака
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Получаем объект
            response = await loop.run_in_executor(
                None,
                lambda: self.s3.get_object(Bucket=self.bucket, Key=file_id)
            )
            
            # Читаем содержимое
            content = response['Body'].read()
            logger.info(f"✅ Файл получен из Yandex Cloud: {file_id}")
            return content
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения из Yandex Cloud: {e}")
            raise
    
    async def delete(self, file_id: str) -> bool:
        """
        Удаляет файл из Яндекс Облака
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.delete_object(Bucket=self.bucket, Key=file_id)
            )
            logger.info(f"✅ Файл удален из Yandex Cloud: {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления из Yandex Cloud: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Получает статистику бакета
        """
        try:
            import boto3
            s3_resource = boto3.resource(
                's3',
                endpoint_url='https://storage.yandexcloud.net',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            bucket = s3_resource.Bucket(self.bucket)
            total_size = 0
            file_count = 0
            
            for obj in bucket.objects.all():
                file_count += 1
                total_size += obj.size
            
            return {
                'provider': 'yandex',
                'total_size': total_size,
                'file_count': file_count,
                'bucket': self.bucket,
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                'provider': 'yandex',
                'total_size': 0,
                'file_count': 0,
                'status': f'error: {str(e)}'
            }