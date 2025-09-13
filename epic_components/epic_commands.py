"""
Epic 限免游戏插件命令组件
处理喜加一查询和订阅相关命令
"""

from typing import List, Tuple, Type, Dict, Any, Optional
import re

from src.common.logger import get_logger
from src.plugin_system import (
    BaseCommand,
    ComponentInfo,
    CommandInfo,
    MaiMessages,
    send_api,
    get_logger
)

from .epic_data_source import EpicDataSource

logger = get_logger("epic_commands")


class EpicFreeCommand(BaseCommand):
    """Epic 限免游戏查询命令"""
    
    command_name = "epic_free"
    command_description = "查询Epic限免游戏"
    command_pattern = r"^(?:[/#])?(?:喜加一|epic|Epic)\s*$"
    intercept_message = True  # 阻断 relay，仅响应命令
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source = None
    
    def initialize(self) -> bool:
        """初始化命令"""
        try:
            if not self.plugin_config:
                logger.error("插件配置未设置")
                return False
                
            self.data_source = EpicDataSource(self.plugin_config)
            return True
        except Exception as e:
            logger.error(f"初始化Epic数据源失败: {e}")
            return False
    
    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        """执行查询命令"""
        try:
            # 确保已初始化
            if not self.data_source:
                if not self.initialize():
                    return False, "数据源初始化失败", True
            
            # 发送正在查询的提示消息
            await self.send_text("🔍 正在查询Epic限免游戏，请稍候...")
            
            # 获取限免游戏信息
            games_info = await self.data_source.get_epic_free()
            
            if not games_info:
                await self.send_text("获取游戏信息失败，请稍后重试。")
                return False, "no_games", True
            
            # 构建文本内容
            if len(games_info) <= 1:
                # 只有头部消息或没有游戏，直接发送
                reply_text = games_info[0] if games_info else "暂未找到限免游戏"
            else:
                # 多个游戏，构建合并消息
                # games_info[0] 是头部消息，games_info[1:] 是游戏列表
                game_count = len(games_info) - 1  # 减去头部消息
                
                # 统计正在免费和即将免费的游戏数量
                current_free_count = 0
                upcoming_free_count = 0
                
                for game_info in games_info[1:]:  # 跳过头部消息
                    if "限免至" in game_info:
                        current_free_count += 1
                    elif "即将于" in game_info:
                        upcoming_free_count += 1
                
                # 构建分类头部消息
                if current_free_count > 0 and upcoming_free_count > 0:
                    header = f"🎮 发现 {game_count} 款Epic限免游戏：\n\n"
                    header += f"🆓 {current_free_count} 款游戏现在免费！\n\n"
                    header += f"⏰ {upcoming_free_count} 款游戏即将免费！\n\n"
                elif current_free_count > 0:
                    header = f"🎮 发现 {current_free_count} 款Epic限免游戏：\n\n"
                    header += f"🆓 {current_free_count} 款游戏现在免费！\n\n"
                elif upcoming_free_count > 0:
                    header = f"🎮 发现 {upcoming_free_count} 款Epic限免游戏：\n\n"
                    header += f"⏰ {upcoming_free_count} 款游戏即将免费！\n\n"
                else:
                    header = f"🎮 发现 {game_count} 款Epic限免游戏：\n\n"
                
                # 分类显示游戏：先显示正在免费的，再显示即将免费的
                current_free_games = []
                upcoming_free_games = []
                
                for game_info in games_info[1:]:  # 跳过头部消息
                    if "限免至" in game_info:
                        current_free_games.append(game_info)
                    elif "即将于" in game_info:
                        upcoming_free_games.append(game_info)
                
                # 按顺序组合游戏列表
                ordered_games = current_free_games + upcoming_free_games
                reply_text = header + "\n\n".join(ordered_games)
            
            # 发送文本消息
            await self.send_text(reply_text)
            
            return True, "ok", True
            
        except Exception as e:
            logger.error(f"执行Epic查询命令失败: {e}")
            try:
                await self.send_text(f"查询失败：{e}")
            except Exception:
                pass
            return False, "exception", True
    


    
