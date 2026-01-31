import bcrypt

class PasswordManager:
    """Менеджер паролей с bcrypt"""
    
    def __init__(self, cost: int = 12):
        self.cost = cost
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = bcrypt.gensalt(rounds=self.cost)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Проверка пароля"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))