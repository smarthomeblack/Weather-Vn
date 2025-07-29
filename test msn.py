import requests
import json
import re
from bs4 import BeautifulSoup


def parse_numeric(value, default=None):

    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        match = re.search(r'^-?\d+\.?\d*', value)
        if match:
            return float(match.group())
    return default


def fetch_and_export_weather_data():

    url = (
        "https://www.msn.com/vi-vn/weather/hourlyforecast/in-Minh-Khai-Commune,T%E1%BB%89nh-Cao-B%E1%BA%B1ng"
    )

    print(f"Đang truy cập URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        script_tag = soup.find('script', id='redux-data')
        if not script_tag:
            print("Lỗi: Không tìm thấy thẻ script nguồn dữ liệu (redux-data).")
            return

        weather_data = json.loads(script_tag.string)
        weather_state = weather_data.get("WeatherData", {}).get("_@STATE@_", {})

        current_condition_raw = weather_state.get("currentCondition", {})
        forecast_days_raw = weather_state.get("forecast", [])
        nowcasting_raw = weather_state.get("nowcasting", {})

        if not current_condition_raw and not forecast_days_raw:
            print("Lỗi: Không tìm thấy dữ liệu thời tiết hiện tại hoặc dự báo trong JSON.")
            return

        precipitation_next_2h_mm = None
        if nowcasting_raw:
            accumulation_data = nowcasting_raw.get("precipitationAccumulation")
            minutes_per_interval = nowcasting_raw.get("minutesBetweenHorrizons")

            if accumulation_data and isinstance(accumulation_data, list) and minutes_per_interval:
                intervals_for_2h = int(120 / minutes_per_interval)
                if len(accumulation_data) >= intervals_for_2h:
                    precipitation_next_2h_mm = accumulation_data[intervals_for_2h - 1]

        current_weather = {
            "condition": current_condition_raw.get('shortCap'),
            "temperature": parse_numeric(current_condition_raw.get('currentTemperature')),
            "feels_like": current_condition_raw.get('feels'),
            "humidity": parse_numeric(current_condition_raw.get('humidity')),
            "precipitation_probability": parse_numeric(current_condition_raw.get("precipitation", {}).get("children")),
            "precipitation_next_2h_mm": precipitation_next_2h_mm,
            "wind_speed_kmh": parse_numeric(current_condition_raw.get('windSpeed')),
            "wind_gust_kmh": parse_numeric(current_condition_raw.get('windGust')),
            "pressure_mb": parse_numeric(current_condition_raw.get('baro')),
            "visibility_km": parse_numeric(current_condition_raw.get('visiblity')),
            "uv_index": current_condition_raw.get('uv'),
            "dew_point": parse_numeric(current_condition_raw.get('dewPoint')),
            "aqi": parse_numeric(current_condition_raw.get('aqi')),
            "primary_pollutant": current_condition_raw.get('primaryPollutant'),
            "rain_forecast": nowcasting_raw.get("summary")
        }

        all_forecasts = []
        for day in forecast_days_raw:
            hourly_forecasts_raw = day.get('hourly', [])

            actual_date = ""
            if hourly_forecasts_raw:
                first_hour_time = hourly_forecasts_raw[0].get('timeStr', '')
                if first_hour_time:
                    actual_date = first_hour_time.split('T')[0]

            if not actual_date:
                actual_date = day.get('day', {}).get('dataValue', '').split('T')[0]

            day_forecast = {
                "date": actual_date,
                "condition": day.get('dayCap'),
                "high_temp": day.get('highTemp'),
                "low_temp": day.get('lowTemp'),
                "summary": " ".join(day.get('summaries', [])),
                "rain_amount_cm": parse_numeric(day.get('rainAmount')),
                "snow_amount_cm": parse_numeric(day.get('snowAmount')),
                "hourly": []
            }

            for hour in hourly_forecasts_raw:
                humidity_val = hour.get('rh', hour.get('humidity'))
                visibility_val = hour.get('vis', hour.get('visibility'))
                hour_data = {
                    "time": hour.get('timeStr', 'N/A').split('T')[1].split('+')[0],
                    "condition": hour.get('cap'),
                    "temperature": hour.get('temperature'),
                    "feels_like": hour.get('feels'),
                    "humidity": parse_numeric(humidity_val),
                    "precipitation_probability": parse_numeric(hour.get('precipitation'), default=0),
                    "rain_amount_cm": hour.get('rainAmount'),
                    "snow_amount_cm": hour.get('snowAmount'),
                    "uv_index": hour.get('uv'),
                    "cloud_cover": parse_numeric(hour.get('cloudCover')),
                    "wind_speed_kmh": parse_numeric(hour.get('windSpeed')),
                    "wind_gust_kmh": parse_numeric(hour.get('windGust')),
                    "visibility_km": parse_numeric(visibility_val),
                    "dew_point": parse_numeric(hour.get('dewPt')),
                    "pressure_mb": parse_numeric(hour.get('airPressure'))
                }
                day_forecast["hourly"].append(hour_data)

            all_forecasts.append(day_forecast)

        final_output = {
            "current_weather": current_weather,
            "forecast": all_forecasts
        }

        output_filename = "test.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=4)

        print(f"\nThành công! Dữ liệu thời tiết hiện tại và dự báo đã được xuất ra tệp '{output_filename}'.")

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi truy cập URL: {e}")
    except json.JSONDecodeError:
        print("Lỗi: Không thể phân tích cú pháp dữ liệu JSON từ thẻ script.")
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}")


if __name__ == '__main__':
    print("Lưu ý: bạn cần cài đặt các thư viện cần thiết để chạy mã này.")
    print("Chạy lệnh sau trong terminal của bạn:")
    print("pip install requests beautifulsoup4")
    fetch_and_export_weather_data()
