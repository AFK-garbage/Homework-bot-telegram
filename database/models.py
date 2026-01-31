import sqlite3
import os
import tempfile
import bcrypt
from datetime import datetime, timedelta
import config


class HomeworkDB:
    """Основной класс для работы с базой данных домашних заданий"""
    
    def __init__(self, db_name: str = None):
        # Определяем папку для файлов
        self.files_dir = self._get_files_directory()
        
        # Используем переданное имя БД или из конфига
        self.db_name = db_name or os.path.join(self.files_dir, config.DB_NAME)
        
        print(f"📁 База данных: {self.db_name}")
        print(f"📁 Папка для файлов: {self.files_dir}")
        
        # Создаем таблицы
        self._create_tables()
    
    def _get_files_directory(self) -> str:
        """Определяем папку для хранения файлов"""
        current_dir = os.getcwd()
        target_dir = os.path.join(current_dir, "HomeWorkBotFiles")
        
        dir_options = [
            target_dir,
            current_dir,
            os.path.join(os.path.expanduser("~"), "HomeWorkBotFiles"),
        ]
        
        for dir_path in dir_options:
            try:
                if dir_path != current_dir:
                    os.makedirs(dir_path, exist_ok=True)
                
                test_file = os.path.join(dir_path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                
                print(f"✅ Выбрана папка: {dir_path}")
                return dir_path
                
            except Exception as e:
                print(f"❌ Не подходит {dir_path}: {e}")
                continue
        
        # Fallback
        temp_dir = tempfile.gettempdir()
        print(f"⚠️ Использую временную папку: {temp_dir}")
        return temp_dir
    
    def _create_tables(self):
        """Создаём таблицы"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS homework (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_id INTEGER NOT NULL, 
                        subject TEXT NOT NULL, 
                        task TEXT NOT NULL, 
                        deadline TEXT NOT NULL, 
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS homework_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        homework_id INTEGER NOT NULL, 
                        storage_id TEXT NOT NULL, 
                        file_type TEXT NOT NULL, 
                        file_name TEXT NOT NULL, 
                        file_size INTEGER, 
                        created_at TEXT NOT NULL, 
                        FOREIGN KEY (homework_id) REFERENCES homework (id) ON DELETE CASCADE
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS moderators (
                        user_id INTEGER PRIMARY KEY, 
                        password_hash TEXT NOT NULL, 
                        created_by INTEGER NOT NULL, 
                        created_at TEXT NOT NULL, 
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
            
            print(f"✅ Все таблицы созданы: {self.db_name}")
            
        except sqlite3.OperationalError as e:
            print(f"❌ Ошибка: {e}")
            self._create_tables_alternative()
    
    def _create_tables_alternative(self):
        """Альтернативный путь создания таблиц"""
        temp_dir = tempfile.gettempdir()
        self.db_name = os.path.join(temp_dir, "homework.db")
        print(f"📁 Использую временную папку: {self.db_name}")
        
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS homework (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER NOT NULL, 
                    subject TEXT NOT NULL, 
                    task TEXT NOT NULL, 
                    deadline TEXT NOT NULL, 
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS homework_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    homework_id INTEGER NOT NULL, 
                    storage_id TEXT NOT NULL, 
                    file_type TEXT NOT NULL, 
                    file_name TEXT NOT NULL, 
                    file_size INTEGER, 
                    created_at TEXT NOT NULL, 
                    FOREIGN KEY (homework_id) REFERENCES homework (id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS moderators (
                    user_id INTEGER PRIMARY KEY, 
                    password_hash TEXT NOT NULL, 
                    created_by INTEGER NOT NULL, 
                    created_at TEXT NOT NULL, 
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
        
        print(f"✅ Таблицы созданы во временной базе")
    
    # === МЕТОДЫ ДЛЯ ФАЙЛОВ ===
    
    def add_files_to_homework(self, homework_id: int, files_data: list):
        """Добавляем несколько файлов к заданию"""
        created_at = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_name) as conn:
            for file_data in files_data:
                conn.execute('''
                    INSERT INTO homework_files 
                    (homework_id, storage_id, file_type, file_name, file_size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    homework_id, 
                    file_data.get('storage_id'),
                    file_data['type'], 
                    file_data['name'], 
                    file_data['size'], 
                    created_at
                ))
    
    def get_all_homework(self):
        """
        Получает ВСЕ домашние задания от ВСЕХ модераторов
        Для показа всем пользователям
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT h.*, 
                       CASE WHEN m.is_active THEN 'Модератор' ELSE 'Пользователь' END as creator_role
                FROM homework h
                LEFT JOIN moderators m ON h.user_id = m.user_id
                ORDER BY h.created_at DESC
            ''')
            return cursor.fetchall()
    
    def get_homework_files(self, homework_id: int):
        """Получаем все файлы задания"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT * FROM homework_files
                WHERE homework_id = ?
                ORDER BY created_at ASC
            ''', (homework_id,))
            return cursor.fetchall()
    
    def get_file_by_id(self, file_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT id, homework_id, storage_id, file_type, file_name, file_size, created_at
                FROM homework_files WHERE id = ?
            ''', (file_id,))
            return cursor.fetchone()
    
    # === МЕТОДЫ ДЛЯ ЗАДАНИЙ ===
    
    def add_homework(self, user_id: int, subject: str, task: str, deadline: str) -> int:
        """Добавляем домашнее задание и возвращаем ID"""
        created_at = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                INSERT INTO homework (user_id, subject, task, deadline, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, subject, task, deadline, created_at))
            return cursor.lastrowid
    
    def get_user_homework(self, user_id: int):
        """Получаем ВСЕ домашние задания пользователя"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT * FROM homework
                WHERE user_id = ?
                ORDER BY deadline ASC
            ''', (user_id,))
            return cursor.fetchall()
    
    def get_homework_by_id(self, homework_id: int, user_id: int = None):
        """
        Получает конкретное задание
        :param homework_id: ID задания
        :param user_id: Если None - не проверяем владельца (доступно всем)
        """
        with sqlite3.connect(self.db_name) as conn:
            if user_id is not None:
                # Для удаления/изменения - проверяем владельца
                cursor = conn.execute('''
                    SELECT * FROM homework
                    WHERE id = ? AND user_id = ?
                ''', (homework_id, user_id))
            else:
                # Для просмотра - без проверки
                cursor = conn.execute('''
                    SELECT * FROM homework
                    WHERE id = ?
                ''', (homework_id,))
            return cursor.fetchone()
    
    def delete_homework(self, homework_id: int, user_id: int):
        """Атомарное удаление задания с файлами"""
        conn = sqlite3.connect(self.db_name)
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # Получаем файлы
            cursor = conn.execute('SELECT storage_id FROM homework_files WHERE homework_id = ?', (homework_id,))
            files = cursor.fetchall()
            
            # Удаляем из БД
            conn.execute('DELETE FROM homework_files WHERE homework_id = ?', (homework_id,))
            conn.execute('DELETE FROM homework WHERE id = ? AND user_id = ?', (homework_id, user_id))
            
            conn.commit()
            return len(files)
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_old_records(self, days=30):
        """Удаляем старые записи"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''
                DELETE FROM homework_files
                WHERE homework_id IN (
                    SELECT id FROM homework WHERE created_at < ?
                )
            ''', (cutoff_date,))
            
            conn.execute('''
                DELETE FROM homework
                WHERE created_at < ?
            ''', (cutoff_date,))
    
    # === МЕТОДЫ ДЛЯ МОДЕРАТОРОВ ===
    
    def create_moderator(self, creator_id: int, user_id: int, password: str) -> bool:
        """Создает нового модератора с хешированием пароля"""
        # Хешируем пароль
        password_hash = self._hash_password(password)
        created_at = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute('''
                    INSERT INTO moderators (user_id, password_hash, created_by, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, password_hash, creator_id, created_at))
                conn.commit()
            return True  # Успешно создан
        except sqlite3.IntegrityError:
            return False  # Модератор уже существует
        except Exception as e:
            print(f"❌ Ошибка создания модератора: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Хеширование пароля с использованием bcrypt"""
        # Генерируем соль (12 раундов = оптимально)
        salt = bcrypt.gensalt(rounds=12)
        # Хешируем пароль + соль
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        # Возвращаем строку (для хранения в БД)
        return hashed.decode('utf-8')
    
    def verify_moderator(self, user_id: int, password: str) -> bool:
        """Проверка пароля модератора"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT password_hash FROM moderators
                WHERE user_id = ? AND is_active = TRUE
            ''', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            stored_hash = result[0]
            
            try:
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    stored_hash.encode('utf-8')
                )
            except:
                return False
    
    def is_moderator(self, user_id: int) -> bool:
        """Проверяем является ли пользователь модератором"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT 1 FROM moderators
                WHERE user_id = ? AND is_active = TRUE
            ''', (user_id,))
            return cursor.fetchone() is not None
    
    def get_all_moderators(self) -> list:
        """Получаем список всех модераторов"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('''
                SELECT user_id, created_by, created_at, is_active
                FROM moderators
            ''')
            return cursor.fetchall()
    
    def deactivate_moderator(self, user_id: int) -> bool:
        """Деактивируем модератора"""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''
                UPDATE moderators SET is_active = FALSE
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            return True