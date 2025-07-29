"""檔案驗證工具函數."""

from typing import Optional
from fastapi import UploadFile


def validate_image_file(file: UploadFile) -> bool:
    """驗證上傳的圖片檔案
    
    Args:
        file: 上傳的檔案物件
        
    Returns:
        bool: 驗證是否通過
    """
    # 檢查檔案大小 (5MB = 5 * 1024 * 1024 bytes)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # 支援的圖片格式
    ALLOWED_CONTENT_TYPES = [
        "image/jpeg",
        "image/jpg", 
        "image/png",
        "image/gif"
    ]
    
    # 支援的副檔名
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif"]
    
    # 檢查內容類型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return False
        
    # 檢查副檔名
    if file.filename:
        file_extension = file.filename.lower().split('.')[-1]
        if f".{file_extension}" not in ALLOWED_EXTENSIONS:
            return False
    
    # 檢查檔案大小 (注意：這裡無法直接檢查大小，需要在讀取時檢查)
    # 實際的大小檢查會在 endpoint 中進行
    
    return True


def format_currency(amount: float) -> str:
    """格式化金額，添加千分位逗號
    
    Args:
        amount: 金額
        
    Returns:
        str: 格式化後的金額字串
    """
    return f"{amount:,.0f}"


def validate_roc_date(date_str: Optional[str]) -> bool:
    """驗證民國年日期格式
    
    Args:
        date_str: 日期字串 (格式: xxx.xx.xx)
        
    Returns:
        bool: 驗證是否通過
    """
    if not date_str:
        return True  # 允許空值
        
    import re
    pattern = r'^\d{1,3}\.\d{1,2}\.\d{1,2}$'
    return bool(re.match(pattern, date_str)) 