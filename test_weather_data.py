"""
Test script để trích xuất dữ liệu thời tiết từ dbtt.edu.vn
Sử dụng: python test_weather_data.py [tỉnh] [huyện]
Ví dụ: python test_weather_data.py hai-duong gia-loc
"""

import requests
from bs4 import BeautifulSoup
import sys
from datetime import datetime, timedelta
import json
import re


# Định nghĩa các mapping cho điều kiện thời tiết
CONDITION_CLASSES = {
    "mưa nhẹ": "rainy",
    "mưa vừa": "pouring",
    "mưa lớn": "pouring",
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

# Các mức độ chất lượng không khí
AIR_QUALITY_LEVEL = {
    "air-1": "Tốt",
    "air-2": "Trung bình thấp",
    "air-3": "Trung bình",
    "air-4": "Kém",
    "air-5": "Xấu",
    "air-6": "Nguy hại"
}


class WeatherVnDataTester:
    """Class to test fetching and processing weather and air quality data."""

    def __init__(self, province, district):
        """Initialize the tester."""
        self.province = province
        self.district = district
        self.url = f"https://dbtt.edu.vn/thoi-tiet-{province}/{district}"

    def get_data(self):
        """Fetch data from dbtt.edu.vn."""
        print(f"Đang tải dữ liệu từ URL: {self.url}")
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as err:
            print(f"Lỗi khi tải dữ liệu: {err}")
            return None

    def parse_current_weather(self, html_content):
        """Parse current weather data from HTML content."""
        if not html_content:
            return None

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            weather_data = {}
            
            # Nhiệt độ hiện tại
            temp_element = soup.select_one(".metro-weather-hi strong")
            if temp_element:
                weather_data["temperature"] = float(temp_element.text.replace("°", ""))

            # Điều kiện thời tiết
            condition_element = soup.select_one(".metro-weather-overview-block-description p")
            if condition_element:
                condition_text = condition_element.text.strip().lower()
                weather_data["condition_text"] = condition_text
                weather_data["condition"] = CONDITION_CLASSES.get(condition_text, "exceptional")

            # Độ ẩm
            humidity_element = soup.select(".metro-weather-conditions li")[0]
            if humidity_element:
                humidity_text = humidity_element.strong.text.replace("%", "")
                weather_data["humidity"] = float(humidity_text)

            # Gió
            wind_element = soup.select(".metro-weather-conditions li")[1]
            if wind_element:
                wind_speed_text = wind_element.strong.text.replace(" m/s", "")
                weather_data["wind_speed"] = float(wind_speed_text)

            # Điểm ngưng
            dewpoint_element = soup.select(".metro-weather-conditions li")[2]
            if dewpoint_element:
                dewpoint_text = dewpoint_element.strong.text.replace("°", "")
                weather_data["dewpoint"] = float(dewpoint_text)

            # Chỉ số UV
            uv_element = soup.select(".metro-weather-conditions li")[3]
            if uv_element:
                uv_text = uv_element.strong.text
                weather_data["uv"] = float(uv_text)

            # Cảm giác như
            apparent_temp_element = soup.select_one(".metro-weather-lo strong")
            if apparent_temp_element:
                weather_data["apparent_temperature"] = float(apparent_temp_element.text.replace("°", ""))

            # Thông tin bình minh / hoàng hôn
            sunrise_element = soup.select_one(".metro-weather-sunrise")
            if sunrise_element:
                sunrise_text = sunrise_element.strong.next_sibling.strip()
                weather_data["sunrise"] = sunrise_text

            sunset_element = soup.select_one(".metro-weather-sunset")
            if sunset_element:
                sunset_text = sunset_element.strong.next_sibling.strip()
                weather_data["sunset"] = sunset_text
                
            return weather_data
        except Exception as err:
            print(f"Lỗi khi phân tích dữ liệu thời tiết hiện tại: {err}")
            return None

    def parse_daily_forecast(self, html_content):
        """Parse daily forecast from HTML content."""
        if not html_content:
            return None

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            forecasts = []
            
            # Tìm phần tử chứa dự báo hàng ngày
            forecast_elements = soup.select(".w_weather_boxes .w_weather")
            
            # Bỏ qua dự báo "Hiện tại" nếu có
            if forecast_elements and "Hiện tại" in forecast_elements[0].select_one(".day b").text:
                forecast_elements = forecast_elements[1:]

            for element in forecast_elements:
                try:
                    forecast_item = {}
                    
                    # Lấy ngày
                    day_element = element.select_one(".day b")
                    if day_element:
                        forecast_item["day_name"] = day_element.text.strip()
                    
                    # Lấy ngày và đổi thành đối tượng datetime
                    date_element = element.select_one(".date")
                    if date_element:
                        date_text = date_element.text.strip()
                        forecast_item["date_text"] = date_text
                        
                        date_parts = date_text.split("/")
                        if len(date_parts) == 2:
                            day, month = map(int, date_parts)
                            year = datetime.now().year
                            forecast_date = datetime(year, month, day).isoformat()
                            forecast_item["datetime"] = forecast_date
                    
                    # Lấy nhiệt độ thấp nhất và cao nhất
                    temp_spans = element.select(".temp span")
                    if len(temp_spans) >= 2:
                        forecast_item["temp_low"] = float(temp_spans[0].text.replace("°", ""))
                        forecast_item["temp_high"] = float(temp_spans[1].text.replace("°", ""))
                    
                    # Lấy điều kiện thời tiết
                    weather_img = element.select_one("img")
                    if weather_img and weather_img.get("alt"):
                        condition_text = weather_img.get("alt").lower()
                        forecast_item["condition_text"] = condition_text
                        forecast_item["condition"] = CONDITION_CLASSES.get(condition_text, "exceptional")
                    
                    forecasts.append(forecast_item)
                except Exception as e:
                    print(f"Lỗi khi xử lý phần tử dự báo theo ngày: {e}")
                    continue
                
            return forecasts
        except Exception as err:
            print(f"Lỗi khi phân tích dữ liệu dự báo theo ngày: {err}")
            return None

    def parse_hourly_forecast(self, html_content):
        """Parse hourly forecast from HTML content."""
        if not html_content:
            return None

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            forecasts = []
            
            # Tìm phần tử chứa dự báo theo giờ
            forecast_elements = soup.select(".weather-time-list .weather-time-item")
            
            for element in forecast_elements:
                try:
                    forecast_item = {}
                    
                    # Lấy giờ
                    time_element = element.select_one(".title")
                    if time_element:
                        time_text = time_element.text.strip()
                        forecast_item["time_text"] = time_text
                        
                        # Chuyển đổi giờ dạng "5:00 pm" thành 24 giờ
                        hour, minute = map(int, time_text[:-3].split(":"))
                        is_pm = "pm" in time_text.lower()
                        
                        if is_pm and hour < 12:
                            hour += 12
                        elif not is_pm and hour == 12:
                            hour = 0
                        
                        now = datetime.now()
                        forecast_time = now.replace(hour=hour, minute=minute)
                        
                        # Nếu giờ dự báo nhỏ hơn giờ hiện tại, đó là dự báo cho ngày mai
                        if forecast_time < now:
                            forecast_time = forecast_time + timedelta(days=1)
                        
                        forecast_item["datetime"] = forecast_time.isoformat()
                    
                    # Lấy nhiệt độ
                    temp_spans = element.select(".temp span")
                    if len(temp_spans) >= 1:
                        forecast_item["temperature"] = float(temp_spans[0].text.replace("°", ""))
                    
                    # Lấy cảm giác như
                    if len(temp_spans) >= 2:
                        forecast_item["apparent_temperature"] = float(temp_spans[1].text.replace("°", ""))
                    
                    # Lấy độ ẩm
                    humidity_element = element.select_one(".humidity span")
                    if humidity_element:
                        humidity_text = humidity_element.text.replace(" %", "")
                        forecast_item["humidity"] = float(humidity_text)
                    
                    # Lấy điều kiện thời tiết
                    condition_element = element.select_one(".desc")
                    if condition_element:
                        condition_text = condition_element.text.lower()
                        forecast_item["condition_text"] = condition_text
                        forecast_item["condition"] = CONDITION_CLASSES.get(condition_text, "exceptional")
                    
                    forecasts.append(forecast_item)
                except Exception as e:
                    print(f"Lỗi khi xử lý phần tử dự báo theo giờ: {e}")
                    continue
                
            return forecasts
        except Exception as err:
            print(f"Lỗi khi phân tích dữ liệu dự báo theo giờ: {err}")
            return None

    def parse_air_quality(self, html_content):
        """Parse air quality data from HTML content."""
        if not html_content:
            return None

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            air_quality_data = {}
            
            # Lấy thông tin về mức độ chất lượng không khí tổng thể
            aqi_content = soup.select_one(".air-quality-content")
            if aqi_content:
                # Lấy class để xác định mức độ (air-1, air-2, ...)
                class_list = aqi_content.get("class", [])
                for cls in class_list:
                    if cls.startswith("air-"):
                        air_quality_data["aqi_level"] = cls
                        air_quality_data["aqi_level_text"] = AIR_QUALITY_LEVEL.get(cls, "Không xác định")
                        break
                
                # Lấy tên mức độ chất lượng không khí
                level_name = aqi_content.select_one(".title")
                if level_name:
                    air_quality_data["aqi"] = level_name.text.strip()
                
                # Lấy mô tả
                desc_element = aqi_content.select_one(".desc")
                if desc_element:
                    air_quality_data["aqi_description"] = desc_element.text.strip()
            
            # Lấy các thông số không khí chi tiết
            air_quality_items = soup.select(".air-quality-item")
            for item in air_quality_items:
                name_elem = item.select_one(".title")
                value_elem = item.select_one("p")
                
                if name_elem and value_elem:
                    name = self._clean_air_quality_name(name_elem.text.strip())
                    value = self._clean_air_quality_value(value_elem.text.strip())
                    
                    if name and value:
                        air_quality_data[name] = float(value)
            
            return air_quality_data
        except Exception as err:
            print(f"Lỗi khi phân tích dữ liệu chất lượng không khí: {err}")
            return None

    def _clean_air_quality_name(self, name):
        """Clean air quality parameter name."""
        name = name.lower()
        
        # Xử lý các tên đặc biệt
        if name == "o3":
            return "o3"
        elif name == "co":
            return "co"
        elif name == "nh3":
            return "nh3"
        elif name == "no":
            return "no"
        elif name == "no2":
            return "no2"
        elif name == "so2":
            return "so2"
        elif "pm2.5" in name or "pm₂.₅" in name:
            return "pm2_5"
        elif "pm10" in name:
            return "pm10"
        
        return None

    def _clean_air_quality_value(self, value):
        """Clean air quality parameter value."""
        # Xóa các ký tự không phải số hoặc dấu chấm
        cleaned = re.sub(r"[^\d.]", "", value)
        if cleaned:
            return cleaned
        
        return None


def get_weather_data(province, district):
    """Lấy tất cả dữ liệu thời tiết và chất lượng không khí."""
    tester = WeatherVnDataTester(province, district)
    html_content = tester.get_data()
    
    if not html_content:
        return None
    
    return {
        "current": tester.parse_current_weather(html_content),
        "daily_forecast": tester.parse_daily_forecast(html_content),
        "hourly_forecast": tester.parse_hourly_forecast(html_content),
        "air_quality": tester.parse_air_quality(html_content)
    }


def print_weather_data(data):
    """In dữ liệu thời tiết ra console."""
    if not data:
        print("Không có dữ liệu để hiển thị")
        return
    
    print("\n=== THÔNG TIN THỜI TIẾT HIỆN TẠI ===")
    for key, value in data["current"].items():
        print(f"{key}: {value}")
    
    print("\n=== DỰ BÁO THEO NGÀY ===")
    for i, forecast in enumerate(data["daily_forecast"]):
        print(f"\nDự báo #{i+1}:")
        for key, value in forecast.items():
            print(f"  {key}: {value}")
    
    print("\n=== DỰ BÁO THEO GIỜ ===")
    # Chỉ hiển thị 5 dự báo giờ đầu tiên để dễ nhìn
    for i, forecast in enumerate(data["hourly_forecast"][:5]):
        print(f"\nDự báo giờ #{i+1}:")
        for key, value in forecast.items():
            print(f"  {key}: {value}")
    
    print(f"\n...và {len(data['hourly_forecast']) - 5} dự báo theo giờ khác.")
    
    print("\n=== CHẤT LƯỢNG KHÔNG KHÍ ===")
    if data["air_quality"]:
        # Thông tin tổng quan
        if "aqi" in data["air_quality"]:
            print(f"Chất lượng không khí: {data['air_quality']['aqi']}")
        if "aqi_level_text" in data["air_quality"]:
            print(f"Mức độ: {data['air_quality']['aqi_level_text']}")
        if "aqi_description" in data["air_quality"]:
            print(f"Mô tả: {data['air_quality']['aqi_description']}")
        
        # Thông số chi tiết
        print("\nCác thông số chi tiết:")
        for key, value in data["air_quality"].items():
            if key not in ["aqi", "aqi_level", "aqi_level_text", "aqi_description"]:
                print(f"  {key}: {value} µg/m³")
    else:
        print("Không có dữ liệu chất lượng không khí")
    
    # Lưu dữ liệu thành file JSON để phân tích chi tiết
    with open("weather_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\nĐã lưu tất cả dữ liệu vào file 'weather_data.json'")


def main():
    """Hàm chính."""
    # Mặc định là Hải Dương, Gia Lộc (với dấu gạch ngang)
    province = "hai-duong"
    district = "gia-loc"
    
    # Kiểm tra tham số dòng lệnh
    if len(sys.argv) > 1:
        province = sys.argv[1]
    if len(sys.argv) > 2:
        district = sys.argv[2]
    
    print(f"Đang lấy dữ liệu thời tiết và chất lượng không khí cho {province}/{district}...")
    weather_data = get_weather_data(province, district)
    
    if weather_data:
        print_weather_data(weather_data)
    else:
        print("Không thể lấy dữ liệu thời tiết.")


if __name__ == "__main__":
    main() 