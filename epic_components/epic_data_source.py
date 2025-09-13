"""
Epic Game Store 数据源模块
提供获取限免游戏信息和订阅管理功能
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from traceback import format_exc

import httpx
from pytz import timezone

from src.common.logger import get_logger

logger = get_logger("epic_data_source")


class EpicDataSource:
    """Epic Game Store 数据源类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.epic_config = config.get("epic", {})
        self.data_config = config.get("data", {})
        self.display_config = config.get("display", {})
        
        # 设置数据目录
        data_dir = self.data_config.get("data_dir", "data/epicfree")
        self.data_path = Path(data_dir)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.pushed_file = self.data_path / self.data_config.get("pushed_file", "last_pushed.json")
    
    
    async def query_epic_api(self) -> List[dict]:
        """
        获取所有 Epic Game Store 促销游戏
        
        参考 RSSHub ``/epicgames`` 路由 https://github.com/DIYgod/RSSHub/blob/master/lib/v2/epicgames/index.js
        """
        
        api_url = self.epic_config.get("api_url", "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions")
        timeout = self.epic_config.get("api_timeout", 10.0)
        retry_count = self.epic_config.get("api_retry_count", 3)
        retry_delay = self.epic_config.get("api_retry_delay", 1.0)
        
        headers = {
            "Referer": self.epic_config.get("referer", "https://www.epicgames.com/store/zh-CN/"),
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": self.epic_config.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"),
        }
        
        params = {
            "locale": self.epic_config.get("locale", "zh-CN"),
            "country": self.epic_config.get("country", "CN"),
            "allowCountries": self.epic_config.get("country", "CN"),
        }
        
        async with httpx.AsyncClient() as client:
            for attempt in range(retry_count + 1):
                try:
                    res = await client.get(
                        api_url,
                        params=params,
                        headers=headers,
                        timeout=timeout,
                    )
                    res_json = res.json()
                    return res_json["data"]["Catalog"]["searchStore"]["elements"]
                except Exception as e:
                    if attempt < retry_count:
                        logger.warning(f"请求 Epic Store API 失败，{retry_delay}秒后重试 (尝试 {attempt + 1}/{retry_count + 1}): {e}")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"请求 Epic Store API 错误 {e.__class__.__name__}\n{format_exc()}")
                        return []
        
        return []
    
    async def get_epic_free(self) -> List[str]:
        """
        获取 Epic Game Store 免费游戏信息
        
        参考 pip 包 epicstore_api 示例 https://github.com/SD4RK/epicstore_api/blob/master/examples/free_games_example.py
        """
        
        games = await self.query_epic_api()
        if not games:
            return [self.display_config.get("error_message", "Epic 可能又抽风啦，请稍后再试（")]
        
        logger.debug(
            f"获取到 {len(games)} 个游戏数据：\n{('、'.join(game['title'] for game in games))}"
        )
        
        game_cnt, msg_list = 0, []
        
        for game in games:
            game_name = game.get("title", "未知")
            try:
                # 检查是否有促销信息
                promotions = game.get("promotions", {})
                if not promotions:
                    logger.debug(f"游戏 {game_name} 没有 promotions 字段，跳过")
                    continue
                
                game_promotions = promotions.get("promotionalOffers", [])
                upcoming_promotions = promotions.get("upcomingPromotionalOffers", [])
                
                logger.debug(f"游戏 {game_name}: 当前促销={bool(game_promotions)}, 即将促销={bool(upcoming_promotions)}")
                original_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
                discount_price = game["price"]["totalPrice"]["fmtPrice"]["discountPrice"]
                
                if not game_promotions and not upcoming_promotions:
                    logger.debug(f"游戏 {game_name} 没有促销信息，跳过")
                    continue  # 跳过没有促销的游戏
                
                # 对于当前免费的游戏，检查是否真的免费
                if game_promotions and game["price"]["totalPrice"]["fmtPrice"]["discountPrice"] != "0":
                    logger.info(f"跳过促销但不免费的游戏：{game_name}({discount_price})")
                    continue
                
                logger.debug(f"游戏 {game_name} 通过过滤，准备处理")
                
                # 处理游戏发行信息
                game_dev, game_pub = game["seller"]["name"], game["seller"]["name"]
                for pair in game["customAttributes"]:
                    if pair["key"] == "developerName":
                        game_dev = pair["value"]
                    elif pair["key"] == "publisherName":
                        game_pub = pair["value"]
                
                dev_com = f"{game_dev} 开发、" if game_dev != game_pub else ""
                companies = (
                    f"由 {dev_com}{game_pub} 发行，"
                    if game_pub != "Epic Dev Test Account"
                    else ""
                )
                
                # 判断是当前免费还是即将免费
                is_current_free = bool(game_promotions)
                is_upcoming_free = bool(upcoming_promotions)
                
                if is_upcoming_free:
                    logger.info(f"发现即将免费游戏：{game_name}")
                
                # 处理游戏限免时间
                if is_current_free:
                    # 当前免费游戏 - 处理结束时间
                    date_rfc3339 = game_promotions[0]["promotionalOffers"][0]["endDate"]
                    end_date = (
                        datetime.strptime(date_rfc3339, "%Y-%m-%dT%H:%M:%S.%f%z")
                        .astimezone(timezone("Asia/Shanghai"))
                        .strftime("%m {m} %d {d} %H:%M")
                        .format(m="月", d="日")
                    )
                    status_text = f"限免至 {end_date}"
                elif is_upcoming_free:
                    # 即将免费游戏 - 处理开始时间
                    date_rfc3339 = upcoming_promotions[0]["promotionalOffers"][0]["startDate"]
                    start_date = (
                        datetime.strptime(date_rfc3339, "%Y-%m-%dT%H:%M:%S.%f%z")
                        .astimezone(timezone("Asia/Shanghai"))
                        .strftime("%m {m} %d {d} %H:%M")
                        .format(m="月", d="日")
                    )
                    status_text = f"即将于 {start_date} 开始限免"
                else:
                    status_text = "限免中"
                
                # 处理游戏商城链接
                if game.get("url"):
                    game_url = game["url"]
                else:
                    slugs = (
                        [
                            x["pageSlug"]
                            for x in game.get("offerMappings", [])
                            if x.get("pageType") == "productHome"
                        ]
                        + [
                            x["pageSlug"]
                            for x in game.get("catalogNs", {}).get("mappings", [])
                            if x.get("pageType") == "productHome"
                        ]
                        + [
                            x["value"]
                            for x in game.get("customAttributes", [])
                            if "productSlug" in x.get("key")
                        ]
                    )
                    game_url = "https://store.epicgames.com/zh-CN{}".format(
                        f"/p/{slugs[0]}" if len(slugs) else ""
                    )
                
                game_cnt += 1
                
                # 构建游戏信息消息
                game_info = f"🎮 {game_name} ({original_price})\n"
                game_info += f"🔗 {game_url}\n"
                
                if self.display_config.get("include_game_description", True):
                    game_info += f"📝 {game['description']}\n"
                
                if self.display_config.get("include_developer_info", True) or self.display_config.get("include_publisher_info", True):
                    game_info += f"🏢 {companies}\n"
                
                if self.display_config.get("include_end_time", True):
                    if is_current_free:
                        game_info += f"⏰ {status_text}，戳上方链接领取吧~"
                    elif is_upcoming_free:
                        game_info += f"⏰ {status_text}，记得关注哦~"
                    else:
                        game_info += f"⏰ {status_text}"
                
                msg_list.append(game_info)
                
            except (AttributeError, IndexError, TypeError) as e:
                logger.warning(f"处理游戏 {game_name} 时遇到错误，可能是即将免费游戏: {e.__class__.__name__}")
                logger.debug(f"错误详情: {format_exc()}")
                # 对于即将免费的游戏，即使出错也尝试添加基本信息
                try:
                    if upcoming_promotions:
                        logger.info(f"尝试添加即将免费游戏 {game_name} 的基本信息")
                        game_info = f"🎮 {game_name} (即将免费)\n"
                        game_info += f"⏰ 即将开始限免，请关注Epic商店\n"
                        msg_list.append(game_info)
                        game_cnt += 1
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"组织 Epic 订阅消息错误 {e.__class__.__name__}\n{format_exc()}")
        
        # 添加头部消息
        if game_cnt > 0:
            header_msg = self.display_config.get("message_template", "{game_count} 款游戏现在免费！").format(game_count=game_cnt)
        else:
            header_msg = self.display_config.get("no_games_message", "暂未找到正在促销的游戏...")
        
        msg_list.insert(0, header_msg)
        return msg_list
    
    
    def check_push(self, msg: List[str]) -> bool:
        """检查是否需要重新推送"""
        
        last_text: List[str] = (
            json.loads(self.pushed_file.read_text(encoding="UTF-8")) if self.pushed_file.exists() else []
        )
        
        need_push = msg != last_text
        if need_push:
            self.pushed_file.write_text(
                json.dumps(msg, ensure_ascii=False, indent=2), encoding="UTF-8"
            )
        return need_push
