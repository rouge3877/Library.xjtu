# Library.xjtu - automatically book seats for you

## Introduction

## Usage

```bash
# 正常使用
python script.py

# 配置错误示例
Config error: Missing required field: 'No'
Exit code: 1

# 网络错误示例
Runtime error: Connection failed: HTTPConnectionPool(...)
Exit code: 2

# 成功预约
Success
Exit code: 0

# 座位已被预约
Seat taken
Exit code: 0
```

## Exit Code
- 0: Success
- 1: Configuration error
- 2: Runtime error (connection error)
- 3: Initialization error
- 4: Failed to post
- 99: Unknown error
