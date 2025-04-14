import json
import sys
import enum
import argparse
import requests
from pathlib import Path
from typing import Tuple, Dict, Optional
from bs4 import BeautifulSoup

class ExitCode(enum.IntEnum):
    """标准化程序退出码"""
    SUCCESS = 0
    CONFIG_ERROR = 1
    RESERVATION_ERROR = 2
    INITIALIZATION_FAILED = 3
    SEAT_OCCUPIED = 4
    SEAT_TAKEN = 5
    UNKNOWN_ERROR = 99

class ReservationStatus(enum.Enum):
    """预约系统状态枚举"""
    AVAILABLE = "Available"
    OCCUPIED = "Occupied by others"
    RESERVED = "Already reserved"
    SUCCESS = "Reservation success"
    TAKEN = "Seat taken"
    UNKNOWN = "Unknown response"

class ConfigError(Exception):
    """配置相关异常基类"""

class ReservationError(Exception):
    """预约业务逻辑异常基类"""

class ConfigManager:
    """配置管理类，支持多源配置加载"""
    REQUIRED_FIELDS = {'No', 'kid', 'sp'}
    DEFAULT_PATHS = [
        Path(".libx.conf"),
        Path.home() / ".libx.conf",
    ]

    def __init__(self):
        self._config = {}
        self._loaded = False

    def _find_config(self, custom_path: Optional[Path] = None) -> Path:
        """定位配置文件路径"""
        if custom_path:
            if not custom_path.exists():
                raise ConfigError(f"Specified config not found: {custom_path}")
            return custom_path

        for path in self.DEFAULT_PATHS:
            if path.exists():
                return path
        raise ConfigError("No valid config found in default locations")

    def load(self, cli_args: Dict[str, str]) -> None:
        """加载并合并配置源"""
        try:
            # 处理配置文件路径
            config_path = self._find_config(cli_args.get("config"))
            with open(config_path) as f:
                file_config = json.load(f)
        except json.JSONDecodeError:
            raise ConfigError(f"Invalid JSON in {config_path}")

        # 合并配置源（命令行参数优先）
        self._config = {**file_config, **{
            k: v for k, v in cli_args.items() 
            if v is not None and k in self.REQUIRED_FIELDS
        }}

        # 验证必需字段
        missing = self.REQUIRED_FIELDS - self._config.keys()
        if missing:
            raise ConfigError(f"Missing required fields: {missing}")

        self._loaded = True

    def get(self, key: str, default: Optional[str] = None) -> str:
        """安全获取配置项"""
        if not self._loaded:
            raise ConfigError("Config not loaded")
        return self._config.get(key, default)

class SeatReserver:
    """座位预约系统核心类"""
    BASE_URL = "http://202.117.24.3:8088/seatuieast/#"
    STATUS_URL = "http://202.117.24.3:8088/quserinfo?cardno={cardno}"

    def __init__(self, config: ConfigManager):
        self.session = requests.Session()
        self.params = {
            'No': config.get('No'),
            'kid': config.get('kid'),
            'sp': config.get('sp')
        }
        self.base_url = config.get('base_url', self.BASE_URL)
        self.cardno = config.get('No')
        self.target_seat = config.get('kid')

    def check_status(self) -> ReservationStatus:
        """检查当前预约状态"""
        try:
            response = self.session.get(
                self.STATUS_URL.format(cardno=self.cardno),
                timeout=10
            )
            data = response.json()

            if data.get('status') == 1:
                if str(data.get('cu')) != self.cardno:
                    return ReservationStatus.OCCUPIED
                if self.target_seat in data.get('message', ''):
                    return ReservationStatus.RESERVED
            return ReservationStatus.AVAILABLE
        except requests.RequestException as e:
            raise ReservationError(f"Status check failed: {str(e)}")

    def initialize(self) -> None:
        """初始化会话连接"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            if not BeautifulSoup(response.text, 'html.parser').find('h2'):
                raise ReservationError("Missing critical page element")
        except requests.RequestException as e:
            raise ReservationError(f"Connection failed: {str(e)}")

    def submit(self) -> Tuple[ReservationStatus, ExitCode]:
        """执行预约请求"""
        try:
            status = self.check_status()
            if status != ReservationStatus.AVAILABLE:
                code = ExitCode.SEAT_OCCUPIED if status == ReservationStatus.OCCUPIED else ExitCode.SUCCESS
                return status, code

            response = self.session.post(self.base_url, data=self.params)
            result = self._parse_response(response.text)
            exit_code = ExitCode.SUCCESS if result == ReservationStatus.SUCCESS else ExitCode.SEAT_TAKEN
            return result, exit_code
        except requests.RequestException as e:
            raise ReservationError(f"Submission failed: {str(e)}")

    def _parse_response(self, html: str) -> ReservationStatus:
        """解析预约响应内容"""
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.find('span').get_text(strip=True) if soup.find('span') else ""

        if '成功' in content and self.target_seat in content:
            return ReservationStatus.SUCCESS
        return ReservationStatus.TAKEN if "已被预约" in content else ReservationStatus.UNKNOWN

def parse_args() -> Dict[str, str]:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Library Seat Reservation System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--config", type=Path, 
                       help="Custom configuration file path")
    parser.add_argument("--No", help="Override user ID (card number)")
    parser.add_argument("--kid", help="Override seat ID")
    parser.add_argument("--sp", help="Override reservation parameter")
    return {k: v for k, v in vars(parser.parse_args()).items() if v is not None}

def main() -> int:
    """主程序入口"""
    try:
        # 参数解析与配置加载
        args = parse_args()
        config = ConfigManager()
        config.load(args)

        # 初始化预约系统
        reserver = SeatReserver(config)
        reserver.initialize()

        # 执行预约流程
        status, exit_code = reserver.submit()
        print(status.value)
        return exit_code.value

    except ConfigError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return ExitCode.CONFIG_ERROR.value
    except ReservationError as e:
        print(f"Reservation Error: {e}", file=sys.stderr)
        return ExitCode.RESERVATION_ERROR.value
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return ExitCode.UNKNOWN_ERROR.value

if __name__ == "__main__":
    sys.exit(main())
