"""Dịch vụ dữ liệu cho Weather Vn."""
from datetime import timedelta
import logging
import re
import aiohttp
from bs4 import BeautifulSoup
from homeassistant.util.dt import utcnow

_LOGGER = logging.getLogger(__name__)


class WeatherVnDataService:
    """Dịch vụ dữ liệu thời tiết từ dbtt.edu.vn."""

    def __init__(self, province, district, scan_interval=30):
        """Khởi tạo dịch vụ với tỉnh và huyện."""
        self.province = province
        self.district = district
        self.base_url = f"https://dbtt.edu.vn/thoi-tiet-{province}/{district}"
        self.forecast_url = f"https://dbtt.edu.vn/thoi-tiet-{province}/{district}/7-ngay-toi"
        self.cache_data = None
        self.cache_time = None
        self.cache_duration = timedelta(minutes=scan_interval)  # Sử dụng thời gian cập nhật từ cấu hình

    async def get_data(self):
        """Lấy dữ liệu thời tiết từ trang web."""
        # Kiểm tra cache
        if self.cache_data and self.cache_time:
            time_diff = utcnow() - self.cache_time
            if time_diff < self.cache_duration:
                _LOGGER.debug("Sử dụng dữ liệu từ cache")
                return self.cache_data

        _LOGGER.debug(f"Tải dữ liệu thời tiết từ {self.base_url}")
        try:
            # Lấy dữ liệu thời tiết hiện tại, chất lượng không khí và dự báo theo giờ
            current_data = await self._fetch_current_data()
            if not current_data:
                return None

            # Lấy dữ liệu dự báo theo ngày từ trang dự báo 7 ngày
            daily_forecast = await self._fetch_daily_forecast()

            # Tổng hợp dữ liệu
            data = {
                **current_data,
                "daily_forecast": daily_forecast
            }

            # Cập nhật cache
            self.cache_data = data
            self.cache_time = utcnow()

            return data

        except Exception as e:
            _LOGGER.error(f"Lỗi khi lấy dữ liệu thời tiết: {str(e)}")
            if self.cache_data:
                _LOGGER.info("Sử dụng dữ liệu cũ từ cache")
                return self.cache_data
            return None

    async def _fetch_current_data(self):
        """Lấy dữ liệu thời tiết hiện tại và dự báo theo giờ."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url) as response:
                    html_content = await response.text()

                    # Phân tích dữ liệu
                    current_weather = await self.parse_current_weather(html_content)
                    hourly_forecast = await self.parse_hourly_forecast(html_content)
                    air_quality = await self.parse_air_quality(html_content)

                    # Tổng hợp dữ liệu
                    return {
                        "current_weather": current_weather,
                        "hourly_forecast": hourly_forecast,
                        "air_quality": air_quality
                    }
        except Exception as e:
            _LOGGER.error(f"Lỗi khi lấy dữ liệu thời tiết hiện tại: {str(e)}")
            return None

    async def _fetch_daily_forecast(self):
        """Lấy dữ liệu dự báo theo ngày từ trang dự báo 7 ngày."""
        try:
            _LOGGER.debug(f"Tải dữ liệu dự báo 7 ngày từ {self.forecast_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.forecast_url) as response:
                    html_content = await response.text()
                    return await self.parse_daily_forecast(html_content)
        except Exception as e:
            _LOGGER.error(f"Lỗi khi lấy dữ liệu dự báo 7 ngày: {str(e)}")
            return []

    async def parse_current_weather(self, html_content):
        """Phân tích dữ liệu thời tiết hiện tại từ HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            result = {}

            # Nhiệt độ hiện tại
            temp_div = soup.select_one('.metro-weather-hi strong')
            if temp_div:
                temp_text = temp_div.text.strip()
                result['temperature'] = float(temp_text.rstrip('°'))

            # Cảm giác nhiệt
            apparent_div = soup.select_one('.metro-weather-lo strong')
            if apparent_div:
                apparent_text = apparent_div.text.strip()
                result['apparent_temperature'] = float(apparent_text.rstrip('°'))

            # Điều kiện thời tiết
            condition_div = soup.select_one('.metro-weather-overview-block-description p')
            if condition_div:
                result['condition'] = condition_div.text.strip()

            # Độ ẩm
            humidity_li = None
            all_li = soup.select('.metro-weather-conditions li')
            for li in all_li:
                if "Độ ẩm" in li.text:
                    humidity_li = li
                    break

            if humidity_li:
                humidity_text = humidity_li.find('strong').text.strip()
                result['humidity'] = float(humidity_text.rstrip('%'))

            # Tốc độ gió
            wind_li = None
            for li in all_li:
                if "Gió" in li.text:
                    wind_li = li
                    break

            if wind_li:
                wind_text = wind_li.find('strong').text.strip()
                result['wind_speed'] = float(wind_text.replace('m/s', '').strip())

            # Điểm ngưng
            dewpoint_li = None
            for li in all_li:
                if "Điểm ngưng" in li.text:
                    dewpoint_li = li
                    break

            if dewpoint_li:
                dewpoint_text = dewpoint_li.find('strong').text.strip()
                result['dew_point'] = float(dewpoint_text.rstrip('°'))

            # Chỉ số UV
            uv_li = None
            for li in all_li:
                if "UV" in li.text:
                    uv_li = li
                    break

            if uv_li:
                uv_text = uv_li.find('strong').text.strip()
                result['uv'] = float(uv_text)

            # Bình minh/hoàng hôn
            sunrise_span = soup.select_one('.metro-weather-sunrise strong')
            sunset_span = soup.select_one('.metro-weather-sunset strong')

            if sunrise_span and sunrise_span.next_sibling:
                sunrise_text = sunrise_span.next_sibling.strip()
                result['sunrise'] = sunrise_text

            if sunset_span and sunset_span.next_sibling:
                sunset_text = sunset_span.next_sibling.strip()
                result['sunset'] = sunset_text

            # Lấy nhiệt độ min/max cho ngày hiện tại từ box dự báo đầu tiên
            try:
                # Tìm box dự báo cho ngày hiện tại
                today_box = soup.find('div', class_='w_weather_boxes').find('div', class_='w_weather')
                if today_box:
                    _LOGGER.debug(f"Tìm thấy box dự báo cho ngày hiện tại: {today_box}")

                    # Tìm tất cả thẻ span trong phần nhiệt độ
                    temp_spans = today_box.select('.temp span')
                    _LOGGER.debug(f"Số thẻ span tìm thấy: {len(temp_spans)}")

                    if len(temp_spans) >= 2:
                        # Thứ tự trong HTML là: min / max
                        temp_min_text = temp_spans[0].text.strip().rstrip('°')
                        temp_max_text = temp_spans[1].text.strip().rstrip('°')

                        _LOGGER.debug(f"Nhiệt độ min: {temp_min_text}, max: {temp_max_text}")

                        result['temp_low'] = float(temp_min_text)
                        result['temp_high'] = float(temp_max_text)
            except Exception as e:
                _LOGGER.error(f"Lỗi khi phân tích nhiệt độ min/max: {str(e)}")

            return result

        except Exception as e:
            _LOGGER.error(f"Lỗi khi phân tích thời tiết hiện tại: {str(e)}")
            return {}

    async def parse_daily_forecast(self, html_content):
        """Phân tích dữ liệu dự báo theo ngày từ HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            forecast_items = []

            # Tìm tất cả các card chứa thông tin dự báo theo ngày
            forecast_cards = soup.select('.weather-detail-content .card')
            if not forecast_cards:
                _LOGGER.warning("Không tìm thấy card dự báo 7 ngày")
                return []

            # Bỏ qua card đầu tiên vì đó là thông tin hiện tại
            forecast_cards = forecast_cards[1:]

            for card in forecast_cards:
                try:
                    item = {}

                    # Lấy ngày và thứ từ tiêu đề
                    title_header = card.select_one('.title-main h2 .weather-date-title')
                    if title_header:
                        title_text = title_header.text.strip()
                        title_parts = title_text.split()
                        if len(title_parts) >= 2:
                            item['day'] = title_parts[0].strip()   # T2, T3, CN...
                            item['date'] = title_parts[1].strip()  # DD/MM

                    # Nhiệt độ
                    temp_p = card.select_one('.weather-main-hero .temp')
                    if temp_p:
                        temp_text = temp_p.text.strip().rstrip('°')
                        if temp_text:
                            item['temperature'] = float(temp_text)

                    # Điều kiện thời tiết
                    condition_p = card.select_one('.weather-main-hero .overview-caption-item-detail')
                    if condition_p:
                        item['condition'] = condition_p.text.strip()

                    # Cảm giác nhiệt
                    apparent_temp_span = card.select_one('.overview-caption-summary-detail span')
                    if apparent_temp_span:
                        apparent_text = apparent_temp_span.text.strip().rstrip('°')
                        if apparent_text:
                            item['apparent_temperature'] = float(apparent_text)

                    # Nhiệt độ min/max
                    temp_low_high = card.select_one('.item-title:-soup-contains("Thấp/Cao")')
                    if temp_low_high:
                        temp_span = temp_low_high.find_next('p').select_one('span')
                        if temp_span:
                            temp_text = temp_span.text.strip()
                            temps = temp_text.split('/')
                            if len(temps) == 2:
                                item['temp_low'] = float(temps[0].strip().rstrip('°'))
                                item['temp_high'] = float(temps[1].strip().rstrip('°'))

                    # Độ ẩm
                    humidity_title = card.select_one('.item-title:-soup-contains("Độ ẩm")')
                    if humidity_title:
                        humidity_p = humidity_title.find_next('p')
                        if humidity_p:
                            humidity_text = humidity_p.text.strip().rstrip('%')
                            if humidity_text:
                                item['humidity'] = float(humidity_text)

                    # Tốc độ gió
                    wind_title = card.select_one('.item-title:-soup-contains("Gió")')
                    if wind_title:
                        wind_p = wind_title.find_next('p')
                        if wind_p:
                            wind_text = wind_p.text.strip().replace('m/s', '').strip()
                            if wind_text:
                                item['wind_speed'] = float(wind_text)

                    # Lượng mưa
                    rain_div = card.select_one('.icon:-soup-contains("Lượng mưa")')
                    if rain_div:
                        rain_p = rain_div.find_next('p')
                        if rain_p:
                            rain_span = rain_p.select_one('span')
                            if rain_span:
                                rain_text = rain_span.text.strip().replace('mm', '').strip()
                                if rain_text:
                                    item['precipitation'] = float(rain_text)

                    # Bình minh/hoàng hôn
                    dawn_title = card.select_one('.item-title:-soup-contains("Bình minh/Hoàng hôn")')
                    if dawn_title:
                        dawn_p = dawn_title.find_next('p')
                        if dawn_p:
                            dawn_text = dawn_p.text.strip()
                            if '/' in dawn_text:
                                dawn_parts = dawn_text.split('/')
                                if len(dawn_parts) == 2:
                                    item['sunrise'] = dawn_parts[0].strip()
                                    item['sunset'] = dawn_parts[1].strip()

                    forecast_items.append(item)
                except Exception as e:
                    _LOGGER.warning(f"Lỗi khi phân tích card dự báo 7 ngày: {str(e)}")
                    continue

            return forecast_items

        except Exception as e:
            _LOGGER.error(f"Lỗi khi phân tích dự báo theo ngày: {str(e)}")
            return []

    async def parse_hourly_forecast(self, html_content):
        """Phân tích dữ liệu dự báo theo giờ từ HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            forecast_items = []

            # Tìm container chứa các dự báo theo giờ
            forecast_container = soup.select_one('.weather-time-list')
            if not forecast_container:
                return []

            # Tìm tất cả các item dự báo theo giờ
            forecast_divs = forecast_container.select('.weather-time-item')

            for div in forecast_divs:
                try:
                    item = {}

                    # Giờ
                    time_div = div.select_one('.title')
                    if time_div:
                        item['time'] = time_div.text.strip()

                    # Nhiệt độ
                    temp_p = div.select_one('.temp')
                    if temp_p:
                        temp_text = temp_p.text.strip()
                        temps = re.findall(r'(\d+\.?\d*)°', temp_text)
                        if len(temps) >= 2:
                            item['temp'] = float(temps[0])
                            item['apparent_temp'] = float(temps[1])

                    # Độ ẩm
                    humidity_p = div.select_one('.humidity span')
                    if humidity_p:
                        humidity_text = humidity_p.text.strip()
                        item['humidity'] = float(humidity_text.rstrip('%'))

                    # Điều kiện thời tiết
                    desc_p = div.select_one('.desc')
                    if desc_p:
                        item['condition'] = desc_p.text.strip()

                    forecast_items.append(item)
                except Exception as e:
                    _LOGGER.warning(f"Lỗi khi phân tích một mục dự báo theo giờ: {str(e)}")
                    continue

            return forecast_items

        except Exception as e:
            _LOGGER.error(f"Lỗi khi phân tích dự báo theo giờ: {str(e)}")
            return []

    async def parse_air_quality(self, html_content):
        """Phân tích dữ liệu chất lượng không khí từ HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            result = {}

            # Tìm container chứa thông tin chất lượng không khí
            air_quality_div = soup.select_one('.air-quality')
            if not air_quality_div:
                return {}

            # Mức độ chất lượng không khí
            level_div = air_quality_div.select_one('.air-quality-content')
            if level_div:
                # Tìm class air-X để xác định cấp độ (1-6)
                classes = level_div.get('class', [])
                air_level = None
                for class_name in classes:
                    if class_name.startswith('air-'):
                        air_level = class_name
                        break

                if air_level:
                    result['level'] = air_level.replace('air-', '')

                # Tiêu đề và mô tả
                title_p = level_div.select_one('.title')
                desc_p = level_div.select_one('.desc')

                if title_p:
                    result['title'] = title_p.text.strip()
                if desc_p:
                    result['description'] = desc_p.text.strip()

            # Các chỉ số chi tiết
            air_items = air_quality_div.select('.air-quality-item')
            for item in air_items:
                title_div = item.select_one('.title')
                value_p = item.select_one('p')

                if title_div and value_p:
                    # Lấy tên chỉ số (loại bỏ thẻ sub nếu có)
                    title = ''.join(title_div.stripped_strings).lower()
                    value = float(value_p.text.strip())

                    # Chuyển đổi tên chỉ số sang key
                    if 'co' in title:
                        result['co'] = value
                    elif 'nh' in title:
                        result['nh3'] = value
                    elif 'no2' in title:
                        result['no2'] = value
                    elif 'no' in title and 'no2' not in title:
                        result['no'] = value
                    elif 'o3' in title or 'o₃' in title:
                        result['o3'] = value
                    elif 'pm2.5' in title or 'pm₂.₅' in title:
                        result['pm2_5'] = value
                    elif 'pm10' in title or 'pm₁₀' in title:
                        result['pm10'] = value
                    elif 'so2' in title or 'so₂' in title:
                        result['so2'] = value

            return result

        except Exception as e:
            _LOGGER.error(f"Lỗi khi phân tích chất lượng không khí: {str(e)}")
            return {}

    def _convert_ug_to_ppm_for_co(self, ug_value):
        """Chuyển đổi từ µg/m³ sang ppm cho CO."""
        # Công thức chuyển đổi: ppm = (µg/m³ * 24.45) / (molecular weight)
        # Phân tử khối của CO là 28.01 g/mol
        try:
            ppm = (float(ug_value) * 24.45) / 28.01
            return round(ppm, 3)
        except (ValueError, TypeError):
            return None
