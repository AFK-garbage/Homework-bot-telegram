# middlewares/rate_limit.py
import time
import asyncio
from typing import Dict, List, Any, Awaitable, Callable
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import logging

logger = logging.getLogger(__name__)


class UserLockMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов и защиты от флуда"""
    
    def __init__(self, 
                 rate_limit: int = 30,
                 window_seconds: int = 60,
                 min_interval: float = 0.5,
                 max_users_in_memory: int = 1000):
        
        super().__init__()
        
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.min_interval = min_interval
        self.max_users_in_memory = max_users_in_memory
        
        self.request_history: Dict[int, List[float]] = defaultdict(list)
        self.processing_users: set[int] = set()
        self.last_message_time: Dict[int, float] = {}
        self.blocked_users: Dict[int, float] = {}
        self.block_duration = 300
        
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 300
        
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limit_hits': 0,
            'flood_hits': 0
        }
        
        print(f"🛡️ UserLockMiddleware инициализирован: {rate_limit} запросов/{window_seconds}сек")
    
    def _cleanup_old_data(self, current_time: float):
        """Периодическая очистка старых данных"""
        if current_time - self.last_cleanup_time < self.cleanup_interval:
            return
        
        print(f"🧹 Очистка памяти... пользователей: {len(self.request_history)}")
        
        # Очищаем историю
        users_to_remove = []
        for user_id, timestamps in self.request_history.items():
            self.request_history[user_id] = [
                t for t in timestamps
                if current_time - t < self.window_seconds * 2
            ]
            if not self.request_history[user_id]:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self.request_history[user_id]
        
        # Очищаем заблокированных
        blocked_to_remove = []
        for user_id, block_time in self.blocked_users.items():
            if current_time - block_time > self.block_duration:
                blocked_to_remove.append(user_id)
        
        for user_id in blocked_to_remove:
            del self.blocked_users[user_id]
            if user_id in self.last_message_time:
                del self.last_message_time[user_id]
        
        # Ограничиваем память
        if len(self.request_history) > self.max_users_in_memory:
            users_sorted = sorted(
                self.request_history.items(),
                key=lambda x: max(x[1]) if x[1] else 0
            )
            users_to_remove = [user_id for user_id, _ in users_sorted[:-self.max_users_in_memory]]
            for user_id in users_to_remove:
                if user_id in self.request_history:
                    del self.request_history[user_id]
                if user_id in self.last_message_time:
                    del self.last_message_time[user_id]
        
        self.processing_users = {
            uid for uid in self.processing_users
            if uid in self.request_history
        }
        
        self.last_cleanup_time = current_time
        print(f"✅ Очистка завершена. Пользователей: {len(self.request_history)}")
    
    def _check_rate_limit(self, user_id: int, current_time: float) -> bool:
        """Проверяет rate limit для пользователя"""
        
        # Проверяем временную блокировку
        if user_id in self.blocked_users:
            block_time = self.blocked_users[user_id]
            if current_time - block_time < self.block_duration:
                time_left = int(self.block_duration - (current_time - block_time))
                print(f"🔒 Пользователь {user_id} заблокирован на {time_left}сек")
                self.stats['blocked_requests'] += 1
                return False
            del self.blocked_users[user_id]
        
        # Проверяем быстрый флуд
        if user_id in self.last_message_time:
            time_diff = current_time - self.last_message_time[user_id]
            if time_diff < self.min_interval:
                print(f"⏰ Анти-флуд: пользователь {user_id} слишком часто пишет")
                self.stats['flood_hits'] += 1
                
                rapid_requests = 0
                for t in self.request_history[user_id][-10:]:
                    if current_time - t < 2.0:
                        rapid_requests += 1
                
                if rapid_requests > 5:
                    self.blocked_users[user_id] = current_time
                    print(f"🚫 Пользователь {user_id} временно заблокирован (флуд)")
                    return False
                
                return False
        
        # Очищаем старые запросы
        self.request_history[user_id] = [
            t for t in self.request_history[user_id]
            if current_time - t < self.window_seconds
        ]
        
        # Проверяем общий лимит
        if len(self.request_history[user_id]) >= self.rate_limit:
            print(f"🚫 Rate limit exceeded: user {user_id} ({len(self.request_history[user_id])}/{self.rate_limit})")
            self.stats['rate_limit_hits'] += 1
            
            if len(self.request_history[user_id]) > self.rate_limit * 2:
                self.blocked_users[user_id] = current_time
                print(f"🚫 Пользователь {user_id} временно заблокирован (превышение лимита)")
            
            return False
        
        # Проверяем, не обрабатывается ли уже
        if user_id in self.processing_users:
            print(f"⏳ Пользователь {user_id} уже обрабатывается")
            
            if user_id in self.last_message_time:
                if current_time - self.last_message_time[user_id] > 30:
                    print(f"⚠️ Снимаю зависшую блокировку для {user_id}")
                    self.processing_users.discard(user_id)
                else:
                    return False
            else:
                return False
        
        return True
    
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """ОСНОВНОЙ МЕТОД MIDDLEWARE"""
        
        
        user_id = event.from_user.id
        current_time = time.time()
        
        
        self.stats['total_requests'] += 1
        
        
        self._cleanup_old_data(current_time)
        
        
        if not self._check_rate_limit(user_id, current_time):
            try:
                if user_id in self.blocked_users:
                    block_time = self.blocked_users[user_id]
                    time_left = int(self.block_duration - (current_time - block_time))
                    await event.answer(
                        f"🚫 Вы временно заблокированы на {time_left} секунд\n"
                        f"Причина: слишком много запросов"
                    )
                elif user_id in self.processing_users:
                    await event.answer("⏳ Подождите, обрабатываю предыдущее сообщение...")
                else:
                    await event.answer("⏳ Слишком много запросов. Подождите немного...")
            except Exception as e:
                print(f"⚠️ Не удалось отправить сообщение о блокировке: {e}")
            
            return
        
        
        self.last_message_time[user_id] = current_time
        self.request_history[user_id].append(current_time)
        
        self.processing_users.add(user_id)
        
        try:
            
            result = await handler(event, data)
            return result
            
        except Exception as e:
            print(f"❌ Ошибка в обработчике для пользователя {user_id}: {e}")
            raise
            
        finally:
            
            if user_id in self.processing_users:
                self.processing_users.remove(user_id)
            
            
            if self.stats['total_requests'] % 100 == 0:
                print(f"📊 Статистика middleware:")
                print(f"   Всего запросов: {self.stats['total_requests']}")
                print(f"   Заблокировано: {self.stats['blocked_requests']}")
                print(f"   Rate limit срабатываний: {self.stats['rate_limit_hits']}")
                print(f"   Флуд срабатываний: {self.stats['flood_hits']}")
                print(f"   Пользователей в памяти: {len(self.request_history)}")