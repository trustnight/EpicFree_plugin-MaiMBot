# Epic 限免游戏插件

MaiMBot版本的Epic Game Store限时可免费领取游戏查询插件。

## 功能特性

- 🎮 查询当前Epic限免游戏
- 📊 丰富的游戏信息展示
- ⚙️ 支持自定义显示选项
- 🔧 灵活的配置控制

## 安装方法

1. 将插件文件夹复制到MaiMBot的`plugins`目录下
2. 确保已安装所需依赖：
   ```bash
   pip install httpx pytz
   ```
3. 重启MaiMBot即可使用

## 文件结构

```
/MaiMBot/plugins/epic_free_plugin/
├── __init__.py                    # 包初始化
├── _manifest.json                 # 插件元信息
├── config.toml                   # 配置文件
├── requirements.txt              # 依赖列表
├── plugin.py                    # 主插件文件
├── test_structure.py            # 结构测试脚本
├── README.md                    # 使用说明
└── epic_components/             # 组件模块目录
    ├── __init__.py              # 组件包初始化
    ├── epic_data_source.py      # 数据源模块
    └── epic_commands.py         # 命令组件
```

## 使用方法

### 查询限免游戏

发送以下命令查询当前限免游戏：
- `/喜加一` 或 `#喜加一` 或 `喜加一`
- `/epic` 或 `#epic` 或 `epic`
- `/Epic` 或 `#Epic` 或 `Epic`

**命令前缀配置**：
- 默认支持 `/`、`#` 或无前缀
- 可在配置文件中设置前缀模式：`slash`、`hash`、`none`、`all`

## 配置说明

插件配置文件为`config.toml`，主要配置项：

### 基本配置
```toml
[plugin]
enabled = true  # 是否启用插件
```

### Epic API配置
```toml
[epic]
api_timeout = 10.0  # API超时时间
api_retry_count = 3  # 重试次数
locale = "zh-CN"  # 地区设置
country = "CN"  # 国家设置
```



### 显示配置
```toml
[display]
max_games = 10  # 最大显示游戏数量
show_price = true  # 是否显示价格信息
show_original_price = true  # 是否显示原价
show_discount = true  # 是否显示折扣信息
include_game_description = true  # 是否包含游戏描述
include_developer_info = true  # 是否包含开发者信息
include_publisher_info = true  # 是否包含发行商信息
include_end_time = true  # 是否包含结束时间
```

## 数据存储

插件会在`data/epicfree`目录下创建以下文件：
- `epic_cache.json` - 游戏数据缓存文件

## 注意事项

1. 插件依赖Epic Game Store的官方API，如果API不可用，查询功能会失效
2. 可以通过配置选项控制显示内容的详细程度
3. 插件支持缓存机制，避免频繁请求API

## 更新日志

### v1.0.0
- 初始版本
- 支持查询限免游戏
- 支持自定义显示选项
- 支持灵活的配置控制

## 许可证

MIT License

## 致谢

- 原插件：[nonebot_plugin_epicfree](https://github.com/monsterxcn/nonebot_plugin_epicfree)
- Epic Game Store API
- MaiMBot 插件系统
