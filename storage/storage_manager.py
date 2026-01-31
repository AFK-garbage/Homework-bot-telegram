import os
import sqlite3
import asyncio
import uuid
import json
import shutil
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from .yandex_storage import YandexCloudStorage
import logging


logger = logging.getLogger(__name__)

# ==================== АБСТРАКТНЫЕ КЛАССЫ ====================

class StorageProvider(ABC):
    """Абстрактный класс для провайдеров хранения"""
    
    @abstractmethod
    async def save(self, file_content: bytes, filename: str, metadata: dict = None) -> Dict[str, Any]:
        """Сохраняет файл, возвращает информацию о сохранении"""
        pass
    
    @abstractmethod
    async def get(self, file_id: str) -> bytes:
        """Получает файл по ID"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Удаляет файл"""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """Статистика использования"""
        pass

# ==================== ЛОКАЛЬНОЕ ХРАНИЛИЩЕ ====================

class LocalStorage(StorageProvider):
    """Локальное хранение на диске"""
    
    def __init__(self, base_path: str = "./storage"):
        self.base_path = os.path.abspath(base_path)
        self._ensure_directory()
        logger.info(f"Локальное хранилище: {self.base_path}")
    
    def _ensure_directory(self):
        """Создает директории если не существуют"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "files"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "metadata"), exist_ok=True)
    
    async def save(self, file_content: bytes, filename: str, metadata: dict = None) -> Dict[str, Any]:
        """Сохраняет файл локально"""
        try:
            # Генерируем уникальный ID для файла
            ext = os.path.splitext(filename)[1] if '.' in filename else '.bin'
            file_id = f"{uuid.uuid4().hex}{ext}"
            
            file_path = os.path.join(self.base_path, "files", file_id)
            meta_path = os.path.join(self.base_path, "metadata", f"{file_id}.json")
            
            # Сохраняем файл на диск
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Создаем информацию о файле
            file_info = {
                'id': file_id,
                'original_name': filename,
                'path': file_path,
                'size': len(file_content),
                'saved_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Сохраняем метаданные в JSON файл
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(file_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Файл сохранен локально: {file_id} ({len(file_content)} байт)")
            return file_info
            
        except Exception as e:
            logger.error(f"Ошибка локального сохранения: {e}")
            raise
    
    async def get(self, file_id: str) -> bytes:
        """Получает файл по ID"""
        try:
            file_path = os.path.join(self.base_path, "files", file_id)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_id}")
            
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Ошибка чтения локального файла: {e}")
            raise
    
    async def delete(self, file_id: str) -> bool:
        """Удаляет файл"""
        try:
            file_path = os.path.join(self.base_path, "files", file_id)
            meta_path = os.path.join(self.base_path, "metadata", f"{file_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if os.path.exists(meta_path):
                os.remove(meta_path)
            
            logger.info(f"Файл удален локально: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления локального файла: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Статистика использования диска"""
        total_size = 0
        file_count = 0
        
        files_dir = os.path.join(self.base_path, "files")
        if os.path.exists(files_dir):
            for file in os.listdir(files_dir):
                file_path = os.path.join(files_dir, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        return {
            'provider': 'local',
            'total_size': total_size,
            'file_count': file_count,
            'path': self.base_path,
            'free_space': shutil.disk_usage(self.base_path).free if os.path.exists(self.base_path) else 0
        }
    
    def cleanup_old_files(self, days: int = 30):
        """Очистка старых файлов"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            files_dir = os.path.join(self.base_path, "files")
            meta_dir = os.path.join(self.base_path, "metadata")
            
            if not os.path.exists(files_dir):
                return
            
            for file in os.listdir(files_dir):
                file_path = os.path.join(files_dir, file)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff:
                        os.remove(file_path)
                        
                        meta_file = os.path.join(meta_dir, f"{file}.json")
                        if os.path.exists(meta_file):
                            os.remove(meta_file)
                        
                        logger.info(f"Удален старый файл: {file}")
                        
        except Exception as e:
            logger.error(f"Ошибка очистки старых файлов: {e}")

# ==================== ОБЛАЧНОЕ ХРАНИЛИЩЕ ====================

class CloudStorage(StorageProvider):
    """Облачное хранилище"""
    
    def __init__(self, provider_type: str = "simulated", config: dict = None):
        self.provider_type = provider_type
        self.config = config or {}
        self.client = None
        logger.info(f"Облачное хранилище: {provider_type}")
    
    async def save(self, file_content: bytes, filename: str, metadata: dict = None) -> Dict[str, Any]:
        """Симуляция облачного сохранения (для тестов)"""
        try:
            # В реальности здесь будет код для AWS S3, Yandex Cloud и т.д.
            # Для тестов просто симулируем сохранение
            await asyncio.sleep(0.1)  # Имитация задержки сети
            
            file_id = f"cloud_{uuid.uuid4().hex}/{filename}"
            
            file_info = {
                'id': file_id,
                'original_name': filename,
                'url': f"https://example.com/{file_id}",
                'size': len(file_content),
                'saved_at': datetime.now().isoformat(),
                'provider': self.provider_type,
                'metadata': metadata or {}
            }
            
            logger.info(f"Файл сохранен в облако (симуляция): {file_id}")
            return file_info
            
        except Exception as e:
            logger.error(f"Ошибка облачного сохранения: {e}")
            raise
    
    async def get(self, file_id: str) -> bytes:
        """Симуляция получения из облака"""
        try:
            await asyncio.sleep(0.1)  # Имитация задержки 
            # В реальности здесь будет запрос к облаку
            return b"simulated_cloud_content"
            
        except Exception as e:
            logger.error(f"Ошибка получения из облака: {e}")
            raise
    
    async def delete(self, file_id: str) -> bool:
        """Симуляция удаления из облака"""
        try:
            await asyncio.sleep(0.1)
            logger.info(f"Файл удален из облака (симуляция): {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления из облака: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Статистика облачного хранилища"""
        return {
            'provider': self.provider_type,
            'total_size': 0,
            'file_count': 0,
            'status': 'simulated'
        }

# ==================== ГИБРИДНОЕ ХРАНИЛИЩЕ ====================

class HybridStorage:
    """Основной класс гибридного хранилища"""
    
    MODES = {
        'local': 'Только локально',
        'cloud': 'Только облако', 
        'both': 'Локально + Облако',
        'mirror': 'Зеркалирование (удаление в обоих)'
    }

    
    def __init__(self, local_config: dict = None, cloud_config: dict = None):

        self.max_file_size_bytes = 50 * 1024 * 1024  # 50MB по умолчанию
        self.auto_cleanup_days = 30
        
        # Инициализация провайдеров
        local_base = local_config.get('base_path', './storage') if local_config else './storage'
        self.local = LocalStorage(local_base)
        
        # Проверяем, настроено ли облако
        self.cloud = None
        if cloud_config and cloud_config.get('enabled', False):
            provider = cloud_config.get('provider', 'simulated')
            self.cloud = CloudStorage(provider, cloud_config)
        
        # Настройки по умолчанию
        self.mode = 'local'
        self.db_path = os.path.join(local_base, 'storage_meta.db')
        self._init_database()
        
        # Автоматическая очистка
        self.auto_cleanup_days = 30
        self.local.cleanup_old_files(self.auto_cleanup_days)

    # Инициализация локального хранилища
        local_base = local_config.get('base_path', './storage') if local_config else './storage'
        self.local = LocalStorage(local_base)
    
    # Инициализация облачного хранилища
        self.cloud = None
        if cloud_config and cloud_config.get('enabled', False):
            # Проверяем, передали ли реальный объект провайдера
            if isinstance(cloud_config.get('provider'), YandexCloudStorage):
                self.cloud = cloud_config['provider']
                logger.info(f"☁️ Инициализировано Yandex Cloud хранилище")
            else:
                # Иначе используем заглушку
                self.cloud = CloudStorage('simulated', {})
                
            logger.info(f"☁️ Инициализировано симулированное облачное хранилище")

        
        logger.info(f"Гибридное хранилище инициализировано. Режим: {self.mode}")
    
    def _init_database(self):
        """Инициализация базы данных для метаинформации"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    original_name TEXT NOT NULL,
                    local_path TEXT,
                    cloud_id TEXT,
                    cloud_provider TEXT,
                    file_size INTEGER,
                    created_at TEXT NOT NULL,
                    storage_mode TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS storage_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON files(created_at)
            ''')
            
            # Сохраняем текущий режим
            conn.execute('''
                INSERT OR REPLACE INTO storage_settings (key, value)
                VALUES ('mode', ?)
            ''', (self.mode,))
            
            conn.commit()
    
    async def save_file(self, file_content: bytes, filename: str, metadata: dict = None) -> Dict[str, Any]:
        """Сохраняет файл согласно текущему режиму"""
        file_size = len(file_content)
        if file_size > self.max_file_size_bytes:
            raise ValueError(
                f"Файл слишком большой! "
                f"Размер: {file_size / 1024 / 1024:.1f} МБ, "
                f"максимум: {self.max_file_size_bytes / 1024 / 1024} МБ"
            )
    
        file_id = str(uuid.uuid4())
        results = {'id': file_id, 'mode': self.mode}
        
        try:
            # РЕЖИМ: Только локально
            if self.mode == 'local':
                local_info = await self.local.save(file_content, filename, metadata)
                results['local'] = local_info
                self._save_to_db(file_id, filename, local_info.get('path'), None, len(file_content), metadata)
            
            # РЕЖИМ: Только облако
            elif self.mode == 'cloud':
                if not self.cloud:
                    raise Exception("Облачное хранилище не настроено")
                
                cloud_info = await self.cloud.save(file_content, filename, metadata)
                results['cloud'] = cloud_info
                self._save_to_db(file_id, filename, None, cloud_info.get('id'), len(file_content), metadata)
            
            # РЕЖИМ: Локально + Облако
            elif self.mode == 'both':
                # Сохраняем локально
                local_info = await self.local.save(file_content, filename, metadata)
                results['local'] = local_info
                
                # Сохраняем в облако (если настроено)
                cloud_id = None
                if self.cloud:
                    try:
                        cloud_info = await self.cloud.save(file_content, filename, metadata)
                        results['cloud'] = cloud_info
                        cloud_id = cloud_info.get('id')
                    except Exception as e:
                        logger.warning(f"Не удалось сохранить в облако: {e}")
                
                self._save_to_db(file_id, filename, local_info.get('path'), cloud_id, len(file_content), metadata)
            
            # РЕЖИМ: Зеркалирование
            elif self.mode == 'mirror':
                if not self.cloud:
                    raise Exception("Для режима mirror нужно облачное хранилище")
                
                # Сохраняем в обоих местах
                local_info = await self.local.save(file_content, filename, metadata)
                cloud_info = await self.cloud.save(file_content, filename, metadata)
                
                results['local'] = local_info
                results['cloud'] = cloud_info
                
                self._save_to_db(file_id, filename, local_info.get('path'), cloud_info.get('id'), len(file_content), metadata)
            
            logger.info(f"Файл сохранен в режиме {self.mode}: {filename}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла: {e}")
            # Откат при ошибке
            await self._rollback_save(results)
            raise
    
    def _save_to_db(self, file_id: str, filename: str, local_path: str, cloud_id: str, size: int, metadata: dict = None):
        """Сохраняет информацию о файле в БД"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO files (id, original_name, local_path, cloud_id, cloud_provider, file_size, created_at, storage_mode, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_id, filename, local_path, cloud_id,
                self.cloud.provider_type if self.cloud else None,
                size, datetime.now().isoformat(), self.mode,
                json.dumps(metadata or {}) if metadata else None
            ))
            conn.commit()
    
    async def _rollback_save(self, results: Dict[str, Any]):
        """Откат сохранения при ошибке"""
        try:
            if 'local' in results and 'id' in results['local']:
                await self.local.delete(results['local']['id'])
            
            if 'cloud' in results and 'id' in results['cloud'] and self.cloud:
                await self.cloud.delete(results['cloud']['id'])
        except Exception as e:
            logger.error(f"Ошибка при откате: {e}")
    
    async def get_file(self, file_id: str) -> Tuple[bytes, Dict[str, Any]]:
        """Получает файл по ID"""
        try:
            # Получаем информацию из БД
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT local_path, cloud_id, storage_mode FROM files WHERE id = ?
                ''', (file_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise FileNotFoundError(f"Файл не найден в БД: {file_id}")
                
                local_path, cloud_id, mode = row
                
                # Пытаемся получить из локального хранилища
                if mode in ['local', 'both', 'mirror'] and local_path:
                    if os.path.exists(local_path):
                        with open(local_path, 'rb') as f:
                            return f.read(), {'source': 'local', 'path': local_path}
                
                # Пытаемся получить из облака
                if mode in ['cloud', 'both', 'mirror'] and cloud_id and self.cloud:
                    try:
                        content = await self.cloud.get(cloud_id)
                        return content, {'source': 'cloud', 'cloud_id': cloud_id}
                    except Exception as e:
                        logger.error(f"Не удалось получить из облака: {e}")
                
                raise FileNotFoundError(f"Файл недоступен: {file_id}")
                
        except Exception as e:
            logger.error(f"Ошибка получения файла {file_id}: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """Удаляет файл"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT local_path, cloud_id, storage_mode FROM files WHERE id = ?
                ''', (file_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                local_path, cloud_id, mode = row
                success = True
                
                # Удаляем из локального хранилища
                if mode in ['local', 'both', 'mirror'] and local_path:
                    if os.path.exists(local_path):
                        try:
                            # Находим ID файла в локальном хранилище
                            file_name = os.path.basename(local_path)
                            await self.local.delete(file_name)
                        except Exception as e:
                            logger.error(f"Ошибка удаления локального файла: {e}")
                            success = False
                
                # Удаляем из облака
                if mode in ['cloud', 'both', 'mirror'] and cloud_id and self.cloud:
                    try:
                        await self.cloud.delete(cloud_id)
                    except Exception as e:
                        logger.error(f"Ошибка удаления из облака: {e}")
                        success = False
                
                # Удаляем запись из БД
                conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
                conn.commit()
                
                logger.info(f"Файл удален: {file_id}")
                return success
                
        except Exception as e:
            logger.error(f"Ошибка удаления файла {file_id}: {e}")
            return False
    
    def switch_mode(self, new_mode: str) -> bool:
        """Переключает режим хранения"""
        if new_mode not in self.MODES:
            logger.error(f"Неизвестный режим: {new_mode}")
            return False
        
        old_mode = self.mode
        self.mode = new_mode
        
        # Сохраняем в БД
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO storage_settings (key, value)
                VALUES ('mode', ?)
            ''', (new_mode,))
            conn.commit()
        
        logger.info(f"Режим хранения изменен: {old_mode} -> {new_mode}")
        return True
    
    def get_current_mode(self) -> Dict[str, Any]:
        """Возвращает текущий режим"""
        return {
            'mode': self.mode,
            'description': self.MODES.get(self.mode, 'Неизвестно'),
            'providers': {
                'local': True,
                'cloud': self.cloud is not None
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика хранилища"""
        local_stats = self.local.get_usage_stats()
        cloud_stats = self.cloud.get_usage_stats() if self.cloud else {'provider': 'not_configured'}
        
        # Получаем количество файлов из БД
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM files')
            total_files = cursor.fetchone()[0]
            
            cursor = conn.execute('''
                SELECT storage_mode, COUNT(*) 
                FROM files 
                GROUP BY storage_mode
            ''')
            files_by_mode = dict(cursor.fetchall())
        
        return {
            'total_files': total_files,
            'files_by_mode': files_by_mode,
            'local': local_stats,
            'cloud': cloud_stats,
            'current_mode': self.mode
        }

# ==================== СИСТЕМА БЭКАПОВ ====================

class BackupSystem:
    """Система автоматических бэкапов"""
    
    def __init__(self, storage: HybridStorage, backup_dir: str = "./backups"):
        self.storage = storage
        self.backup_dir = os.path.abspath(backup_dir)
        self._ensure_backup_dir()
        
        # Настройки бэкапов
        self.backup_interval_days = 3
        self.keep_backups = 5
        
        logger.info(f"Система бэкапов: {self.backup_dir}, интервал: {self.backup_interval_days} дней")
    
    def _ensure_backup_dir(self):
        """Создает директорию для бэкапов"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, "full"), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, "logs"), exist_ok=True)
    
    async def create_backup(self, backup_type: str = "full") -> Dict[str, Any]:
        """Создает бэкап"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{backup_type}_backup_{timestamp}"
            
            backup_path = os.path.join(self.backup_dir, "full", f"{backup_name}.zip")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Бэкап базы данных хранилища
                if os.path.exists(self.storage.db_path):
                    zipf.write(self.storage.db_path, "storage_meta.db")
                
                # Бэкап локальных файлов
                local_files_dir = os.path.join(self.storage.local.base_path, "files")
                if os.path.exists(local_files_dir):
                    for root, dirs, files in os.walk(local_files_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.storage.local.base_path)
                            zipf.write(file_path, arcname)
                
                # Добавляем информацию о бэкапе
                settings = {
                    'backup_type': backup_type,
                    'created_at': datetime.now().isoformat(),
                    'storage_mode': self.storage.mode,
                    'file_count': self._count_files(local_files_dir) if os.path.exists(local_files_dir) else 0
                }
                
                zipf.writestr("backup_info.json", json.dumps(settings, indent=2))
            
            # Записываем лог
            self._log_backup(backup_name, backup_path, backup_type)
            
            # Очищаем старые бэкапы
            self._cleanup_old_backups()
            
            logger.info(f"Бэкап создан: {backup_name}")
            return {
                'name': backup_name,
                'path': backup_path,
                'type': backup_type,
                'size': os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                'created_at': timestamp
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            raise
    
    def _count_files(self, directory: str) -> int:
        """Считает файлы в директории"""
        count = 0
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                count += len(files)
        return count
    
    def _log_backup(self, backup_name: str, backup_path: str, backup_type: str):
        """Записывает лог бэкапа"""
        log_file = os.path.join(self.backup_dir, "logs", "backup_history.log")
        
        log_entry = {
            'name': backup_name,
            'path': backup_path,
            'type': backup_type,
            'created_at': datetime.now().isoformat(),
            'size': os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def _cleanup_old_backups(self):
        """Удаляет старые бэкапы"""
        try:
            backup_dir = os.path.join(self.backup_dir, "full")
            if not os.path.exists(backup_dir):
                return
            
            backups = []
            for file in os.listdir(backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(backup_dir, file)
                    backups.append((file_path, os.path.getmtime(file_path)))
            
            # Сортируем по времени (новые сначала)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Удаляем старые, оставляем только keep_backups
            for backup_path, _ in backups[self.keep_backups:]:
                os.remove(backup_path)
                logger.info(f"Удален старый бэкап: {os.path.basename(backup_path)}")
                
        except Exception as e:
            logger.error(f"Ошибка очистки бэкапов: {e}")
    
    async def start_auto_backups(self, days_interval: int = 3):
        """Запускает автоматические бэкапы каждые N дней"""
        logger.info(f"🚀 Автоматические бэкапы запущены (каждые {days_interval} дней)")
        
        while True:
            try:
                await asyncio.sleep(60 * 60)  # Проверяем каждый час
                
                # Ищем последний бэкап
                backup_dir = os.path.join(self.backup_dir, "full")
                if not os.path.exists(backup_dir):
                    # Если папки нет, создаем первый бэкап
                    await self.create_backup("full")
                    continue
                
                backups = []
                for file in os.listdir(backup_dir):
                    if file.endswith('.zip'):
                        file_path = os.path.join(backup_dir, file)
                        backups.append((file_path, os.path.getmtime(file_path)))
                
                if not backups:
                    # Нет бэкапов - создаем первый
                    await self.create_backup("full")
                else:
                    # Находим самый новый бэкап
                    latest_backup = max(backups, key=lambda x: x[1])
                    last_time = datetime.fromtimestamp(latest_backup[1])
                    days_since = (datetime.now() - last_time).days
                    
                    if days_since >= days_interval:
                        logger.info(f"⏰ Прошло {days_since} дней, создаю новый бэкап")
                        await self.create_backup("full")
                    else:
                        days_left = days_interval - days_since
                        logger.debug(f"⏳ До следующего бэкапа: {days_left} дней")
                        
            except Exception as e:
                logger.error(f"Ошибка в авто-бэкапе: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке