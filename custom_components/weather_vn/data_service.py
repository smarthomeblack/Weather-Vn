"""Dịch vụ dữ liệu cho Weather Vn."""
import asyncio
import json
import logging
import re
from typing import Any
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse

from .const import _PROVINCES_DATA, ACTIVITY_MAP

_LOGGER = logging.getLogger(__name__)


class WeatherVnDataError(Exception):
    """Lỗi tùy chỉnh cho việc lấy dữ liệu của Weather Vn."""
    pass


def _parse_numeric(value, default=None):
    """
    Phân tích một cách an toàn một giá trị số từ một chuỗi có thể chứa các đơn vị,
    hoặc trả về giá trị nếu nó đã là một số. Luôn trả về float.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"^-?\d+\.?\d*", value)
        if match:
            return float(match.group())
    if default is not None:
        return float(default)
    return None


class WeatherVnDataService:
    """Dịch vụ dữ liệu thời tiết từ dbtt.edu.vn."""

    def __init__(self, province: str, district: str):
        """Khởi tạo dịch vụ với tỉnh và huyện."""
        self.province = province
        self.district = district
        self.msn_url = self._build_msn_url()
        self.dbtt_url = f"https://dbtt.edu.vn/thoi-tiet-{province}/{district}"

    def _build_msn_url(self) -> str:
        """Xây dựng URL cho MSN Weather."""
        province_name = _PROVINCES_DATA.get(self.province, {}).get("name", self.province)
        district_name = _PROVINCES_DATA.get(
            self.province, {}
        ).get("districts", {}).get(self.district, self.district)
        location_string = f"{district_name},{province_name}"
        # Mã hóa chuỗi sang định dạng URL
        encoded_location = urllib.parse.quote(location_string)
        return f"https://www.msn.com/vi-vn/weather/forecast/in-{encoded_location}"

    def _build_msn_life_url(self) -> str:
        """Xây dựng URL cho trang life của MSN dựa trên tỉnh và huyện."""
        location_name = f"{self.district}, {self.province}".replace("Tỉnh ", "").replace("Thành phố ", "")
        encoded_location = urllib.parse.quote(location_name)
        return f"https://www.msn.com/vi-vn/weather/life/in-{encoded_location}"

    async def get_data(self) -> dict[str, Any]:
        """
        Lấy dữ liệu từ cả hai nguồn. Ném ra WeatherVnDataError nếu nguồn dữ liệu
        quan trọng (MSN) thất bại.
        """
        async with aiohttp.ClientSession() as session:
            # Sử dụng asyncio.gather để thực hiện các yêu cầu mạng đồng thời
            results = await asyncio.gather(
                self._fetch_msn_weather(session),
                self._fetch_dbtt_aqi(session),
                self._fetch_msn_life_data(session),  # Thêm tác vụ mới
                return_exceptions=True,  # Trả về exception thay vì ném ra ngay lập tức
            )

        msn_data, aqi_data, life_data = results

        # Xử lý kết quả từ MSN
        if isinstance(msn_data, Exception):
            _LOGGER.debug("Không thể lấy dữ liệu thời tiết từ MSN. Lỗi: %s", msn_data)
            # Nếu MSN lỗi, chúng ta không thể tiếp tục
            raise WeatherVnDataError("Lỗi khi lấy dữ liệu thời tiết từ MSN") from msn_data

        # Xử lý kết quả từ DBTT
        if isinstance(aqi_data, Exception):
            _LOGGER.debug(
                "Không thể lấy dữ liệu AQI từ dbtt.edu.vn, sẽ bỏ qua: %s", aqi_data
            )
            aqi_data = {}  # Sử dụng dữ liệu AQI rỗng

        # Xử lý kết quả từ MSN Life
        if isinstance(life_data, Exception):
            _LOGGER.debug("Không thể lấy dữ liệu hoạt động từ MSN, sẽ bỏ qua: %s", life_data)
            life_data = {"activities": []}  # Sử dụng dữ liệu rỗng

        # Kết hợp dữ liệu
        combined_data = {
            **msn_data,
            "air_quality": aqi_data,
            **life_data,  # Thêm dữ liệu hoạt động
        }

        _LOGGER.debug("Đã cập nhật dữ liệu tổng hợp thành công")
        return combined_data

    async def _fetch_msn_weather(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Lấy và phân tích dữ liệu thời tiết từ MSN."""
        _LOGGER.debug(f"Đang tải dữ liệu thời tiết từ MSN: {self.msn_url}")
        try:
            async with session.get(self.msn_url) as response:
                response.raise_for_status()
                html_content = await response.text()

                soup = BeautifulSoup(html_content, 'html.parser')
                redux_script = soup.find('script', {'id': 'redux-data'})
                if not redux_script:
                    raise WeatherVnDataError("Không tìm thấy thẻ script 'redux-data' trong HTML của MSN")

                json_data = json.loads(redux_script.string)
                return self._parse_msn_json(json_data)

        except aiohttp.ClientResponseError as http_err:
            _LOGGER.debug("Lỗi HTTP khi tải dữ liệu MSN: %s, url='%s'", http_err.status, http_err.request_info.url)
            raise WeatherVnDataError(f"Lỗi HTTP {http_err.status}") from http_err
        except Exception as e:
            _LOGGER.debug(f"Lỗi không xác định khi xử lý dữ liệu MSN: {e}")
            raise WeatherVnDataError("Lỗi không xác định") from e

    async def _fetch_msn_life_data(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Lấy và phân tích dữ liệu hoạt động đời sống từ MSN."""
        life_url = self._build_msn_life_url()
        _LOGGER.debug(f"Đang tải dữ liệu hoạt động từ MSN: {life_url}")
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }
        try:
            async with session.get(life_url, headers=headers) as response:
                response.raise_for_status()
                html_content = await response.text()

                soup = BeautifulSoup(html_content, 'html.parser')
                redux_script = soup.find('script', {'id': 'redux-data'})
                if not redux_script:
                    _LOGGER.debug("Không tìm thấy thẻ script 'redux-data' trong trang life của MSN")
                    return {"activities": []}

                json_data = json.loads(redux_script.string)
                return self._parse_msn_life_data(json_data)
        except Exception as e:
            _LOGGER.debug(f"Lỗi khi tải hoặc phân tích dữ liệu hoạt động từ MSN: {e}")
            return {"activities": []}  # Không ném lỗi, chỉ trả về rỗng

    def _parse_msn_life_data(self, json_data: dict) -> dict:
        """Phân tích dữ liệu JSON từ trang life của MSN."""
        try:
            life_activity_data = self._find_key_recursively(json_data, 'lifeActivityData')
            if not life_activity_data:
                return {"activities": []}

            days_data = life_activity_data.get('days')
            if not days_data or not isinstance(days_data, list) or len(days_data) == 0:
                return {"activities": []}

            today_indices = days_data[0].get('lifeDailyIndices')
            if not today_indices or not isinstance(today_indices, list):
                return {"activities": []}

            activities = []
            for item in today_indices:
                item_type = item.get("type")
                item_sub_type = item.get("subType")
                activity_name = ACTIVITY_MAP.get((item_type, item_sub_type))

                if activity_name:
                    activities.append({
                        "name": activity_name,
                        "state": item.get("taskbarSummary"),
                        "summary": item.get("summary"),
                        "type": item_type,
                        "subType": item_sub_type
                    })

            return {"activities": activities}
        except (KeyError, IndexError):
            return {"activities": []}

    def _find_key_recursively(self, data, target_key):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_key:
                    return value
                elif isinstance(value, (dict, list)):
                    result = self._find_key_recursively(value, target_key)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_key_recursively(item, target_key)
                if result is not None:
                    return result
        return None

    def _parse_msn_json(self, json_data: dict) -> dict:
        """Phân tích dữ liệu JSON từ MSN và ánh xạ sang cấu trúc mong muốn."""
        weather_state = json_data.get("WeatherData", {}).get("_@STATE@_", {})

        # --- Gom các nguồn dữ liệu thô ---
        current_raw = weather_state.get("currentCondition", {})
        forecast_days_raw = weather_state.get("forecast", [])
        today_forecast_raw = forecast_days_raw[0] if forecast_days_raw else {}
        hourly_forecast_raw = today_forecast_raw.get("hourly", []) if today_forecast_raw else []
        first_hour_raw = hourly_forecast_raw[0] if hourly_forecast_raw else {}

        # Lấy xác suất mưa của giờ tiếp theo
        next_hour_precip_prob = 0.0
        precipitation_next_hour_amount = 0.0
        precipitation_next_hour_accumulation = 0.0
        if len(hourly_forecast_raw) > 1:
            next_hour_forecast = hourly_forecast_raw[1]
            next_hour_precip_prob = _parse_numeric(next_hour_forecast.get("precipitation"), default=0)
            precipitation_next_hour_amount = _parse_numeric(next_hour_forecast.get("rainAmount"), default=0) * 10
            precipitation_next_hour_accumulation = _parse_numeric(next_hour_forecast.get("raAccu"), default=0) * 10

        # --- Dữ liệu thời tiết hiện tại ---
        current_weather = {}
        if current_raw:
            current_weather = {
                "temperature": _parse_numeric(current_raw.get("currentTemperature")),
                "apparent_temperature": _parse_numeric(current_raw.get("feels")),
                "condition": current_raw.get("shortCap"),
                "humidity": _parse_numeric(current_raw.get("humidity")),
                "wind_speed": _parse_numeric(current_raw.get("windSpeed"), default=0) / 3.6,
                "wind_gust": _parse_numeric(current_raw.get("windGust")),
                "dew_point": _parse_numeric(current_raw.get("dewPoint")),
                "uv": _parse_numeric(current_raw.get("uv")),
                "pressure": _parse_numeric(current_raw.get("baro")),
                "visibility": _parse_numeric(current_raw.get("visiblity")),
                "precipitation_amount": _parse_numeric(first_hour_raw.get("rainAmount"), default=0) * 10,
                "precipitation_accumulation": _parse_numeric(first_hour_raw.get("raAccu"), default=0) * 10,
                "precipitation_probability": next_hour_precip_prob,
                "precipitation_next_hour_amount": precipitation_next_hour_amount,
                "precipitation_next_hour_accumulation": precipitation_next_hour_accumulation,
                "sunrise": today_forecast_raw.get("almanac", {}).get("sunrise", "").split("T")[-1],
                "sunset": today_forecast_raw.get("almanac", {}).get("sunset", "").split("T")[-1],
                "temp_low": _parse_numeric(today_forecast_raw.get("lowTemp")),
                "temp_high": _parse_numeric(today_forecast_raw.get("highTemp")),
                "precipitation_today": _parse_numeric(today_forecast_raw.get("raToMN"), default=0) * 10,
            }

        # --- Dự báo hàng giờ ---
        hourly_forecast = []
        # MSN trả về dự báo hàng giờ cho nhiều ngày, ta chỉ lấy 48 giờ đầu
        hour_count = 0
        for day in forecast_days_raw:
            if hour_count >= 48:
                break
            for hour in day.get("hourly", []):
                if hour_count >= 48:
                    break

                hourly_item = {
                    "datetime": hour.get("timeStr"),
                    "temperature": _parse_numeric(hour.get("temperature")),
                    "apparent_temperature": _parse_numeric(hour.get("feels")),
                    "humidity": _parse_numeric(hour.get("humidity")),
                    "condition": hour.get("cap"),
                    "precipitation_probability": _parse_numeric(hour.get("precipitation"), default=0),
                    "wind_speed": _parse_numeric(hour.get("windSpeed"), default=0) / 3.6,  # km/h -> m/s
                }
                hourly_forecast.append(hourly_item)
                hour_count += 1

        # --- Dự báo hàng ngày ---
        daily_forecast = []
        for day in forecast_days_raw:
            daily_item = {
                "datetime": day.get("almanac", {}).get("valid", "").split("T")[0],
                "condition": day.get("dayCap"),
                "temp_high": _parse_numeric(day.get("highTemp")),
                "temp_low": _parse_numeric(day.get("lowTemp")),
                "precipitation_probability": _parse_numeric(day.get("day", {}).get("precipitation"), default=0),
                "precipitation": _parse_numeric(day.get("raToMN"), default=0) * 10,  # Lấy raToMN (cm) và đổi sang mm
                "humidity": _parse_numeric(day.get("day", {}).get("humidity")),
                "wind_speed": _parse_numeric(day.get("windSpeed"), default=0) / 3.6,  # km/h -> m/s
                "sunrise": day.get("almanac", {}).get("sunrise", "").split("T")[-1],
                "sunset": day.get("almanac", {}).get("sunset", "").split("T")[-1],
            }
            daily_forecast.append(daily_item)

        return {
            "current_weather": current_weather,
            "hourly_forecast": hourly_forecast,
            "daily_forecast": daily_forecast,
        }

    async def _fetch_dbtt_aqi(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Lấy và phân tích dữ liệu chất lượng không khí từ dbtt.edu.vn."""
        _LOGGER.debug(f"Đang tải dữ liệu AQI từ dbtt: {self.dbtt_url}")
        try:
            async with session.get(self.dbtt_url) as response:
                response.raise_for_status()
                html_content = await response.text()
                parsed_aqi = await self.parse_air_quality(html_content)
                _LOGGER.debug("Dữ liệu AQI đã phân tích từ dbtt: %s", parsed_aqi)
                return parsed_aqi
        except Exception as e:
            # Lỗi này không nghiêm trọng, chỉ ghi lại cảnh báo
            _LOGGER.debug("Lỗi khi tải dữ liệu AQI từ dbtt: %s", e)
            return {}

    async def parse_air_quality(self, html_content: str) -> dict[str, Any]:
        """Phân tích dữ liệu chất lượng không khí từ HTML của dbtt.edu.vn."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            result = {}

            air_quality_div = soup.select_one('.air-quality')
            if not air_quality_div:
                return {}

            level_div = air_quality_div.select_one('.air-quality-content')
            if level_div:
                classes = level_div.get('class', [])
                for class_name in classes:
                    if class_name.startswith('air-'):
                        result['level'] = class_name
                        break

                title_p = level_div.select_one('.title')
                desc_p = level_div.select_one('.desc')
                if title_p:
                    result['title'] = title_p.text.strip()
                if desc_p:
                    result['description'] = desc_p.text.strip()

            air_items = air_quality_div.select('.air-quality-item')
            for item in air_items:
                title_div = item.select_one('.title')
                value_p = item.select_one('p')
                if title_div and value_p:
                    title = ''.join(title_div.stripped_strings).lower()
                    value = _parse_numeric(value_p.text.strip())
                    key_map = {
                        'co': 'co', 'nh': 'nh3', 'no2': 'no2', 'no': 'no',
                        'o3': 'o3', 'o₃': 'o3',
                        'pm2.5': 'pm2_5', 'pm₂.₅': 'pm2_5',
                        'pm10': 'pm10', 'pm₁₀': 'pm10',
                        'so2': 'so2', 'so₂': 'so2'
                    }
                    for title_key, result_key in key_map.items():
                        if title_key in title:
                            result[result_key] = value
                            break
            return result
        except Exception as e:
            _LOGGER.debug("Lỗi khi phân tích dữ liệu AQI từ dbtt: %s", e)
            return {}

    def _convert_ug_to_ppm_for_co(self, ug_value):
        """Chuyển đổi từ µg/m³ sang ppm cho CO. Giữ lại để tương thích."""
        try:
            # Phân tử khối của CO là 28.01 g/mol
            ppm = (float(ug_value) * 24.45) / 28.01
            return round(ppm, 3)
        except (ValueError, TypeError):
            return None
