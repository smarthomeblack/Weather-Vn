"""Hằng số cho tích hợp Weather Vn."""
import json
import os
from typing import Dict, Any
from homeassistant.core import HomeAssistant

DOMAIN = "weather_vn"


# Đường dẫn tới thư mục hiện tại
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


# Đọc dữ liệu từ file JSON - phiên bản đồng bộ
def _load_json_data_sync(filename: str) -> Dict[str, Any]:
    """Tải dữ liệu từ tệp JSON."""
    file_path = os.path.join(_CURRENT_DIR, "data", filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Trả về dict rỗng nếu file không tồn tại hoặc không phải là JSON hợp lệ
        return {}


# Đọc dữ liệu từ file JSON - phiên bản bất đồng bộ
async def _load_json_data_async(hass: HomeAssistant, filename: str) -> Dict[str, Any]:
    """Tải dữ liệu từ tệp JSON (phiên bản không đồng bộ)."""
    return await hass.async_add_executor_job(_load_json_data_sync, filename)


# KHÔNG DÙNG phương thức đồng bộ trong config flow
async def load_json_data(hass: HomeAssistant, filename: str) -> Dict[str, Any]:
    """Tải dữ liệu JSON không đồng bộ."""
    return await hass.async_add_executor_job(_load_json_data_sync, filename)


# Đọc dữ liệu từ file provinces_districts.json - CHỈ DÙNG KHI KHỞI TẠO MODULE
_PROVINCES_DATA = {}
try:
    file_path = os.path.join(_CURRENT_DIR, "data", "provinces_districts.json")
    with open(file_path, "r", encoding="utf-8") as f:
        _PROVINCES_DATA = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

# Các thành phố/tỉnh hỗ trợ
PROVINCES = {province_id: province_data["name"]
             for province_id, province_data in _PROVINCES_DATA.items()}

# Các quận/huyện hỗ trợ
DISTRICTS = {}
for province_data in _PROVINCES_DATA.values():
    DISTRICTS.update(province_data.get("districts", {}))

# Condition mapping từ MSN sang Home Assistant
CONDITION_CLASSES = {
    # ---- Logic ánh xạ theo yêu cầu của người dùng ----

    # sunny: Dành cho các trạng thái có nắng nhưng không hoàn toàn quang đãng.
    "nắng rải rác": "sunny",
    "nắng gián đoạn": "sunny",
    "có nắng": "sunny",
    "có nắng": "sunny",  # Biến thể
    "trời nhiều nắng": "sunny",
    "nắng đẹp": "sunny",

    # partlycloudy: Dành cho các trạng thái trời quang, trong hoặc chỉ có ít mây.
    "bầu trời quang đãng": "partlycloudy",
    "trời quang": "partlycloudy",
    "quang đãng": "partlycloudy",
    "ít mây": "partlycloudy",
    "trời trong": "partlycloudy",
    "mây thưa": "partlycloudy",
    "mây cụm": "partlycloudy",
    "có mây rải rác": "partlycloudy",
    "hơi có mây": "partlycloudy",
    "mây rải rác": "partlycloudy",
    "có mây": "partlycloudy",

    # cloudy: Dành cho các trạng thái nhiều mây, âm u.
    "nhiều mây": "cloudy",
    "Nhiều mây": "cloudy",
    "mây đen u ám": "cloudy",
    "mây che kín": "cloudy",
    "trời âm u": "cloudy",
    "âm u": "cloudy",
    "u ám": "cloudy",

    # pouring: Mưa lớn.
    "mưa rào": "pouring",
    "mưa lớn": "pouring",
    "mưa to": "pouring",
    "mưa cường độ nặng": "pouring",
    "mưa rất nặng": "pouring",
    "mưa như trút nước": "pouring",
    "mưa rào lớn": "pouring",

    # rainy: Mưa nhỏ.
    "mưa rào nhỏ": "rainy",
    "mưa nhẹ": "rainy",
    "mưa vừa": "rainy",
    "mưa phùn": "rainy",
    "mưa bay": "rainy",
    "có mưa": "rainy",
    "mưa nhỏ": "rainy",
    # lightning-rainy & lightning: Dông, sét.
    "dông": "lightning-rainy",
    "dông rải rác": "lightning-rainy",
    "mưa dông": "lightning-rainy",
    "sấm sét": "lightning",

    # clear-night: Trời trong về đêm.
    "trời trong xanh": "clear-night",
    "trời trong, đêm": "clear-night",
    "Trời trong xanh": "clear-night",
    "trời ít mây": "clear-night",
    # Các điều kiện đặc biệt khác.
    "sương mù": "fog",
    "sương mù nhẹ": "fog",
    "gió mạnh": "windy",
    "trời gió": "windy",
    "gió lớn": "windy",
    "mưa tuyết": "snowy-rainy",
    "mưa đá": "hail",
    "tuyết": "snowy",
    "bão": "exceptional",
    "khác thường": "exceptional",
}


# Các hằng số cho cảm biến chất lượng không khí (từ dbtt.edu.vn)
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

# Bảng ánh xạ cứng cho các hoạt động đời sống do người dùng cung cấp
ACTIVITY_MAP = {
    (1, 1): "Quần Áo",
    (1, 2): "Chỉ số UV",
    (1, 3): "Phong hàn",
    (1, 4): "Sốc nhiệt",
    (2, 10): "Ô",
    (2, 12): "Lái xe",
    (3, 20): "Hoạt động ngoài trời",
    (3, 21): "Làm vườn",
    (3, 22): "Đi bộ",
    (3, 24): "Chạy bộ",
    (3, 25): "Dã ngoại",
    (3, 26): "Đi xe đạp",
    (3, 27): "Thiên văn",
}
