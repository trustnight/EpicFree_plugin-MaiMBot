"""
Epic 限免游戏插件主文件
MaiMBot版本的Epic Game Store限免游戏插件
"""

from typing import List, Tuple, Type, Dict, Any

from src.common.logger import get_logger
from src.plugin_system import (
    BasePlugin,
    BaseCommand,
    register_plugin,
    CommandInfo,
    ConfigField,
)

from .epic_components import EpicFreeCommand

logger = get_logger("epic_free_plugin")


@register_plugin
class EpicFreePlugin(BasePlugin):
    """Epic 限免游戏插件"""
    
    plugin_name: str = "epic_free_plugin"
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = ["httpx>=0.24.0", "pytz>=2023.3"]
    config_file_name: str = "config.toml"
    
    config_schema: Dict[str, Any] = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
        },
        "epic": {
            "api_url": ConfigField(type=str, default="https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions", description="Epic API地址"),
            "api_timeout": ConfigField(type=float, default=10.0, description="API超时时间（秒）"),
            "api_retry_count": ConfigField(type=int, default=3, description="API重试次数"),
            "api_retry_delay": ConfigField(type=float, default=1.0, description="API重试延迟（秒）"),
            "user_agent": ConfigField(type=str, default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36", description="User-Agent"),
            "referer": ConfigField(type=str, default="https://www.epicgames.com/store/zh-CN/", description="Referer"),
            "locale": ConfigField(type=str, default="zh-CN", description="地区设置"),
            "country": ConfigField(type=str, default="CN", description="国家设置"),
        },
        "data": {
            "cache_duration": ConfigField(type=int, default=300, description="缓存持续时间（秒）"),
            "cache_file": ConfigField(type=str, default="epic_cache.json", description="缓存文件名"),
        },
        "display": {
            "max_games": ConfigField(type=int, default=10, description="最大显示游戏数量"),
            "show_price": ConfigField(type=bool, default=True, description="是否显示价格信息"),
            "show_original_price": ConfigField(type=bool, default=False, description="是否显示原价"),
            "show_discount": ConfigField(type=bool, default=False, description="是否显示折扣信息"),
            "include_game_description": ConfigField(type=bool, default=False, description="是否包含游戏描述"),
            "include_developer_info": ConfigField(type=bool, default=False, description="是否包含开发者信息"),
            "include_publisher_info": ConfigField(type=bool, default=False, description="是否包含发行商信息"),
            "include_end_time": ConfigField(type=bool, default=True, description="是否包含结束时间"),
        },
    }
    
    def get_plugin_components(self) -> List[Tuple[CommandInfo, Type[BaseCommand]]]:
        """返回插件包含的命令组件列表"""
        components = []
        
        if self.get_config("plugin.enabled", True):
            # 添加命令组件
            components.append((EpicFreeCommand.get_command_info(), EpicFreeCommand))
        
        return components
    