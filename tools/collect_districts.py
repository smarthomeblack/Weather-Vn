#!/usr/bin/env python3
"""
Script để thu thập danh sách đầy đủ các quận/huyện từ tất cả các tỉnh
trên trang web dbtt.edu.vn
"""

import json
import os
import re
import time
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Danh sách các tỉnh
PROVINCES = {
    # Đông Bắc Bộ
    "ha-giang": "Hà Giang",
    "cao-bang": "Cao Bằng",
    "bac-kan": "Bắc Kạn",
    "tuyen-quang": "Tuyên Quang",
    "thai-nguyen": "Thái Nguyên",
    "lang-son": "Lạng Sơn",
    "quang-ninh": "Quảng Ninh",
    "bac-giang": "Bắc Giang",
    "phu-tho": "Phú Thọ",

    # Tây Bắc Bộ
    "lao-cai": "Lào Cai",
    "dien-bien": "Điện Biên",
    "lai-chau": "Lai Châu",
    "son-la": "Sơn La",
    "yen-bai": "Yên Bái",
    "hoa-binh": "Hoà Bình",

    # Đồng bằng Sông Hồng
    "ha-noi": "Hà Nội",
    "vinh-phuc": "Vĩnh Phúc",
    "bac-ninh": "Bắc Ninh",
    "hai-duong": "Hải Dương",
    "hai-phong": "Hải Phòng",
    "hung-yen": "Hưng Yên",
    "thai-binh": "Thái Bình",
    "ha-nam": "Hà Nam",
    "nam-dinh": "Nam Định",
    "ninh-binh": "Ninh Bình",

    # Bắc Trung Bộ
    "thanh-hoa": "Thanh Hóa",
    "nghe-an": "Nghệ An",
    "ha-tinh": "Hà Tĩnh",
    "quang-binh": "Quảng Bình",
    "quang-tri": "Quảng Trị",
    "hue": "Huế",

    # Nam Trung Bộ
    "da-nang": "Đà Nẵng",
    "quang-nam": "Quảng Nam",
    "quang-ngai": "Quảng Ngãi",
    "binh-dinh": "Bình Định",
    "phu-yen": "Phú Yên",
    "khanh-hoa": "Khánh Hoà",
    "ninh-thuan": "Ninh Thuận",
    "binh-thuan": "Bình Thuận",

    # Tây Nguyên
    "kon-tum": "Kon Tum",
    "gia-lai": "Gia Lai",
    "dak-lak": "Đắk Lắk",
    "dak-nong": "Đắk Nông",
    "lam-dong": "Lâm Đồng",

    # Đông Nam Bộ
    "binh-phuoc": "Bình Phước",
    "tay-ninh": "Tây Ninh",
    "binh-duong": "Bình Dương",
    "dong-nai": "Đồng Nai",
    "ba-ria-vung-tau": "Bà Rịa - Vũng Tàu",
    "ho-chi-minh": "Hồ Chí Minh",

    # Đồng bằng sông Cửu Long
    "long-an": "Long An",
    "tien-giang": "Tiền Giang",
    "ben-tre": "Bến Tre",
    "tra-vinh": "Trà Vinh",
    "vinh-long": "Vĩnh Long",
    "dong-thap": "Đồng Tháp",
    "an-giang": "An Giang",
    "kien-giang": "Kiên Giang",
    "can-tho": "Cần Thơ",
    "hau-giang": "Hậu Giang",
    "soc-trang": "Sóc Trăng",
    "bac-lieu": "Bạc Liêu",
    "ca-mau": "Cà Mau",
}


def normalize_district_id(district_name, url_path):
    """
    Chuẩn hóa ID quận/huyện từ URL hoặc tên
    """
    # Nếu URL chứa đường dẫn, lấy phần cuối cùng làm ID
    if '/' in url_path:
        district_id = url_path.split('/')[-1]
        return district_id

    # Nếu không có URL hợp lệ, tạo ID từ tên
    district_id = district_name.lower()

    # Chuyển các ký tự tiếng Việt về không dấu và thay thế khoảng trắng bằng dấu gạch
    vietnamese_chars = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
    }

    for vietnamese, latin in vietnamese_chars.items():
        district_id = district_id.replace(vietnamese, latin)

    # Thay thế các ký tự đặc biệt và khoảng trắng bằng dấu gạch ngang
    district_id = re.sub(r'[^a-z0-9]', '-', district_id)

    # Loại bỏ các dấu gạch ngang liên tiếp
    district_id = re.sub(r'-+', '-', district_id)

    # Loại bỏ dấu gạch ngang ở đầu và cuối
    district_id = district_id.strip('-')

    return district_id


def get_districts_for_province(province_id, province_name):
    """
    Truy cập trang tỉnh và lấy danh sách các quận/huyện
    """
    url = f"https://dbtt.edu.vn/thoi-tiet-{province_id}"
    districts = {}

    try:
        print(f"Đang lấy dữ liệu cho {province_name}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Cách 1: Tìm phần có tiêu đề "Thời tiết quận huyện [tên tỉnh]"
        district_section = None

        # Tìm tất cả các thẻ div có class="weather-city mt-20"
        weather_city_divs = soup.find_all('div', class_='weather-city mt-20')
        if weather_city_divs:
            for div in weather_city_divs:
                # Tìm tiêu đề h3 trong div
                title = div.find('h3')
                if title and (
                    "quận huyện" in title.text.lower() or
                    "xã phường" in title.text.lower() or
                    province_name.lower() in title.text.lower()
                ):
                    district_section = div
                    break

        if district_section:
            # Tìm danh sách quận/huyện từ section
            district_list = district_section.find('ul', class_='weather-city-inner')

            if district_list:
                for li in district_list.find_all('li'):
                    a_tag = li.find('a')
                    if a_tag:
                        district_name = a_tag.text.strip()
                        district_url = a_tag.get('href', '')

                        # Phân tích URL để lấy ID quận/huyện
                        if district_url:
                            parsed_url = urlparse(district_url)
                            path_parts = parsed_url.path.strip('/').split('/')

                            if len(path_parts) > 2:
                                district_id = path_parts[-1]
                                districts[district_id] = district_name
                            else:
                                # Tạo ID từ tên nếu không thể trích xuất từ URL
                                district_id = normalize_district_id(district_name, "")
                                districts[district_id] = district_name
                        else:
                            # Tạo ID từ tên nếu không có URL
                            district_id = normalize_district_id(district_name, "")
                            districts[district_id] = district_name

                print(f"Đã tìm thấy {len(districts)} quận/huyện cho {province_name}")
            else:
                print(f"Không tìm thấy danh sách quận/huyện cho {province_name} (không có ul.weather-city-inner)")
        else:
            print(f"Không tìm thấy phần quận/huyện cho {province_name} (không có div.weather-city)")

            # Thử tìm theo cách khác nếu không có tiêu đề rõ ràng
            # Tìm tất cả các liên kết có chứa tên tỉnh
            links = soup.find_all('a')
            province_path = f"/thoi-tiet-{province_id}/"
            district_count = 0
            for link in links:
                href = link.get('href', '')
                if province_path in href and href != province_path and href.count('/') >= 3:
                    district_name = link.text.strip()
                    if district_name:
                        path_parts = href.strip('/').split('/')
                        if len(path_parts) > 2:
                            district_id = path_parts[-1]
                            districts[district_id] = district_name
                            district_count += 1

            if district_count > 0:
                print(f"Đã tìm thấy {district_count} quận/huyện cho {province_name} bằng phương pháp thay thế")

    except Exception as e:
        print(f"Lỗi khi truy cập {url}: {str(e)}")

    # Thêm thời gian nghỉ để không gửi quá nhiều yêu cầu
    time.sleep(1)

    return districts


def main():
    """
    Hàm chính để thu thập dữ liệu từ tất cả các tỉnh
    """
    results = {}

    # Thu thập dữ liệu cho từng tỉnh
    for province_id, province_name in PROVINCES.items():
        results[province_id] = {
            "name": province_name,
            "districts": get_districts_for_province(province_id, province_name)
        }

    # Tạo thư mục data nếu chưa tồn tại
    data_dir = os.path.join(os.path.dirname(__file__), "..", "custom_components", "weather_vn", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Lưu dữ liệu vào file JSON
    output_file = os.path.join(data_dir, "provinces_districts.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Đã lưu dữ liệu vào {output_file}")

    # Tổng kết
    total_districts = sum(len(prov_data["districts"]) for prov_data in results.values())
    print(f"Tổng cộng: {len(results)} tỉnh/thành phố, {total_districts} quận/huyện")


if __name__ == "__main__":
    main()
