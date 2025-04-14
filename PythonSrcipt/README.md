# 📚 Library Seat Reservation System

一个用于图书馆座位预约的命令行工具，支持配置文件和命令行参数的混合配置，自动初始化登录并尝试预约指定座位，并返回结果状态。


## 🛠 功能概览

- 🧾 从配置文件或命令行加载预约参数
- 🛰️ 自动检测当前预约状态（是否已被他人或自己占用）
- 🔒 会话初始化与页面连通性校验
- 📬 提交预约请求，解析预约结果
- 🧭 明确的异常处理与退出码


## 🧩 依赖环境

- Python ≥ 3.7
- 依赖库：
  ```bash
  pip install requests beautifulsoup4
  ```


## 📁 配置说明

系统支持通过 JSON 格式的配置文件提供参数，也支持命令行参数覆盖。

### 必需配置字段（无论是配置文件还是命令行）：

| 字段名 | 含义 |
|--------|------|
| `No`   | 用户卡号（学号或一卡通） |
| `kid`  | 目标座位编号 |
| `sp`   | 预约参数（通常为时间段或预约类型） |

### 可选字段：

| 字段名      | 含义                             | 默认值 |
|-------------|----------------------------------|--------|
| `base_url`  | 系统首页地址                     | `http://202.117.24.3:8088/seatuieast/#` |

### 配置文件默认搜索路径：

程序将优先查找以下路径之一作为默认配置文件：

- 当前目录下的 `.libx.conf`
- 用户主目录下的 `.libx.conf`（如 `~/.libx.conf`）

### 示例配置 `.libx.conf`：

```json
{
  "No": "2022012345",
  "kid": "A123",
  "sp": "1"
}
```


## 🚀 使用方法

### 1. 直接运行（使用默认配置文件）：

```bash
python reserver.py
```

### 2. 使用命令行参数覆盖：

```bash
python reserver.py --No 2022012345 --kid A123 --sp 1
```

### 3. 指定配置文件路径：

```bash
python reserver.py --config /path/to/my_config.json
```

## 📊 退出码定义

程序以不同的退出码标识当前执行结果或错误状态：

| 退出码 | 名称                 | 说明 |
|--------|----------------------|------|
| 0      | SUCCESS              | 预约成功或已预约 |
| 1      | CONFIG_ERROR         | 配置错误 |
| 2      | RESERVATION_ERROR    | 预约逻辑失败 |
| 3      | INITIALIZATION_FAILED| 会话初始化失败 |
| 4      | SEAT_OCCUPIED        | 座位被他人占用 |
| 5      | SEAT_TAKEN           | 预约失败，已被抢占 |
| 99     | UNKNOWN_ERROR        | 未知错误 |


## 🧪 示例输出

```bash
Reservation success
```

或

```bash
Occupied by others
```

或标准错误输出：

```bash
Configuration Error: Missing required fields: {'No'}
```


## 📦 模块结构说明

| 类/函数            | 功能描述 |
|---------------------|----------|
| `ConfigManager`     | 加载并校验配置参数 |
| `SeatReserver`      | 预约系统核心逻辑 |
| `ReservationStatus` | 标识当前预约状态 |
| `ExitCode`          | 标准退出码定义 |
| `parse_args()`      | 解析命令行参数 |
| `main()`            | 程序主入口 |


## 🧯 异常处理机制

程序定义了两类核心异常：

- `ConfigError`：配置相关问题
- `ReservationError`：业务逻辑异常，如网络错误、预约冲突等

所有异常都会输出详细信息至 `stderr` 并对应返回错误退出码。


## 📌 注意事项

- 此脚本假设目标图书馆预约系统页面结构稳定，若结构变动可能需修改 `BeautifulSoup` 解析逻辑。
- 程序请求地址是硬编码的，请确保 `BASE_URL` 和 `STATUS_URL` 可用，或通过配置项修改。


## 📄 License

本项目仅供学习与研究用途，禁止用于任何未经授权的自动化占位行为。

