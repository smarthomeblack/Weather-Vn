"""Constants for Weather Vn integration."""
import json
import os
from typing import Dict, Any
from homeassistant.core import HomeAssistant

DOMAIN = "weather_vn"


# Đường dẫn tới thư mục hiện tại
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


# Đọc dữ liệu từ file JSON - phiên bản đồng bộ
def _load_json_data_sync(filename: str) -> Dict[str, Any]:
    """Load data from JSON file (synchronous version)."""
    file_path = os.path.join(_CURRENT_DIR, "data", filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Trả về dict rỗng nếu file không tồn tại hoặc không phải là JSON hợp lệ
        return {}


# Đọc dữ liệu từ file JSON - phiên bản bất đồng bộ
async def _load_json_data_async(hass: HomeAssistant, filename: str) -> Dict[str, Any]:
    """Load data from JSON file (async version)."""
    return await hass.async_add_executor_job(_load_json_data_sync, filename)


# Phiên bản không async cho quá trình cài đặt ban đầu
def _load_json_data(filename: str) -> Dict[str, Any]:
    """Backward compatible method to load JSON data."""
    return _load_json_data_sync(filename)


# Đọc dữ liệu từ file provinces_districts.json
_PROVINCES_DATA = _load_json_data_sync("provinces_districts.json")

# Các thành phố/tỉnh hỗ trợ
PROVINCES = {province_id: province_data["name"]
             for province_id, province_data in _PROVINCES_DATA.items()}

# Các quận/huyện hỗ trợ
DISTRICTS = {}
for province_data in _PROVINCES_DATA.values():
    DISTRICTS.update(province_data.get("districts", {}))

# Condition mapping từ DBTT sang Home Assistant
CONDITION_CLASSES = {
    "mưa nhẹ": "rainy",
    "mưa vừa": "pouring",
    "mưa lớn": "pouring",
    "mưa cường độ nặng": "pouring",
    "mưa rất nặng": "pouring",
    "bầu trời quang đãng": "sunny",
    "mây cụm": "partlycloudy",
    "mây rải rác": "cloudy",
    "mây thưa": "partlycloudy",
    "mây đen u ám": "cloudy",
    "sấm sét": "lightning",
    "trời trong, đêm": "clear-night",
    "nhiều mây": "cloudy",
    "khác thường": "exceptional",
    "sương mù": "fog",
    "bão": "exceptional",
    "mây che kín": "cloudy",
}

# Các hằng số cho cảm biến chất lượng không khí
AIR_QUALITY_LEVEL = {
    "air-1": "Tốt",
    "air-2": "Trung bình thấp",
    "air-3": "Trung bình",
    "air-4": "Kém",
    "air-5": "Xấu",
    "air-6": "Nguy hại"
}

AQI_DESCRIPTION = {
    "air-1": "Chất lượng không khí tốt, không có rủi ro về sức khỏe.",
    "air-2": (
        "Chất lượng không khí chấp nhận được, tuy nhiên nhạy cảm với ô nhiễm "
        "không khí có thể gặp các triệu chứng nhẹ."
    ),
    "air-3": (
        "Không tốt cho người nhạy cảm. Nhóm người nhạy cảm có thể chịu ảnh hưởng sức khỏe. "
        "Số đông không có nguy cơ bị tác động."
    ),
    "air-4": (
        "Nhóm người nhạy cảm trải qua ảnh hưởng nghiêm trọng sức khỏe. "
        "Ảnh hưởng sức khỏe người thường."
    ),
    "air-5": (
        "Cảnh báo sức khỏe: Mọi người có thể trải qua các ảnh hưởng sức khỏe. "
        "Nhóm người nhạy cảm trải qua ảnh hưởng nghiêm trọng sức khỏe."
    ),
    "air-6": "Cảnh báo sức khỏe: Mọi người có thể trải qua các ảnh hưởng sức khỏe nghiêm trọng."
}

# Đơn vị đo chất lượng không khí
AIR_QUALITY_UNITS = {
    "co": "µg/m³",
    "nh3": "µg/m³",
    "no": "µg/m³",
    "no2": "µg/m³",
    "o3": "µg/m³",
    "pm2_5": "µg/m³",
    "pm10": "µg/m³",
    "so2": "µg/m³"
}

DEFAULT_NAME = "Weather Vn"
CONF_PROVINCE = "province"
CONF_DISTRICT = "district"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30  # Thời gian cập nhật mặc định là 30 phút
ATTRIBUTION = "Dữ liệu được cung cấp bởi dbtt.edu.vn"
