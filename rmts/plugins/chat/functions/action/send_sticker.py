import os
import aiofiles

from io import BytesIO
from pathlib import Path
from typing import Optional, List

from nonebot.log import logger

class SendSticker:
    
    def __init__(self, relative_path: str = "rmts/resources/images/stickers", file_extension: str = ".png"):
        """
        Args:
            relative_path: 相对于 cwd 的路径
            file_extension: 文件扩展名
        """
        self.sticker_directory = Path(os.getcwd()) / relative_path
        self.file_extension = file_extension
        self._sticker_cache = None

        logger.info(f"表情包路径{self.sticker_directory}")
    
    def get_sticker_list(self) -> List[str]:
        """获取贴纸目录下所有指定扩展名文件的文件名（不含扩展名）"""
        if self._sticker_cache is None:
            if not self.sticker_directory.exists():
                self._sticker_cache = []
            else:
                self._sticker_cache = [f.stem for f in self.sticker_directory.glob(f"*{self.file_extension}")]
        
        return self._sticker_cache
    
    def get_sticker_path(self, filename: str) -> Optional[Path]:
        """通过文件名获取贴纸的完整路径
        
        Args:
            filename: 贴纸文件名（不含扩展名）
            
        Returns:
            完整路径，如果文件不存在则返回 None
        """
        sticker_list = self.get_sticker_list()
        
        if filename not in sticker_list:
            return None
        
        return self.sticker_directory / f"{filename}{self.file_extension}"
    
    async def get_sticker_bytes(self, filename: str) -> Optional[BytesIO]:
        """通过文件名获取贴纸的 BytesIO 对象
        
        Args:
            filename: 贴纸文件名(不含扩展名)
            
        Returns:
            BytesIO 对象,如果文件不存在则返回 None
        """
        
        sticker_path = self.get_sticker_path(filename)
        
        if sticker_path is None:
            return None
        
        async with aiofiles.open(sticker_path, "rb") as f:
            content = await f.read()
            return BytesIO(content)
