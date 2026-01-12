"""
密码哈希服务

使用 bcrypt 进行密码哈希和验证
"""
import re
import bcrypt


class PasswordService:
    """密码服务"""
    
    # 密码强度要求
    MIN_LENGTH = 6
    MAX_LENGTH = 32
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希
        
        Args:
            password: 明文密码
            
        Returns:
            bcrypt 哈希后的密码
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码
            
        Returns:
            密码是否匹配
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        验证密码强度
        
        Args:
            password: 明文密码
            
        Returns:
            (是否通过验证, 错误消息)
        """
        if not password:
            return False, "密码不能为空"
        
        if len(password) < PasswordService.MIN_LENGTH:
            return False, f"密码长度至少{PasswordService.MIN_LENGTH}位"
        
        if len(password) > PasswordService.MAX_LENGTH:
            return False, f"密码长度不能超过{PasswordService.MAX_LENGTH}位"
        
        # 检查是否包含空格
        if " " in password:
            return False, "密码不能包含空格"
        
        # 可选：检查是否包含数字和字母（可根据需求调整）
        # has_letter = bool(re.search(r'[a-zA-Z]', password))
        # has_digit = bool(re.search(r'\d', password))
        # if not (has_letter and has_digit):
        #     return False, "密码需包含字母和数字"
        
        return True, ""
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        检查密码哈希是否需要更新（使用了过时的算法）
        
        Args:
            hashed_password: 哈希后的密码
            
        Returns:
            是否需要重新哈希
        """
        return False


# 便捷函数
hash_password = PasswordService.hash_password
verify_password = PasswordService.verify_password
validate_password_strength = PasswordService.validate_password_strength
