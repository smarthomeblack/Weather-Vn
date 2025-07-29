import requests
import json
from bs4 import BeautifulSoup
import os

URL = "msn"
RAW_DATA_FILE = "life_data.json"
ACTIVITIES_OUTPUT_FILE = "activities.json"
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    )
}

ACTIVITY_MAP = {
    (1, 1): "Quần Áo",
    (1, 2): "Chỉ số UV",
    (1, 3): "Phong hàn",
    (1, 4): "Sốc nhiệt",
    (2, 10): "Ô",
    (2, 12): "Lái xe",
    (3, 20): "Đi xe đạp",
    (3, 21): "Làm vườn",
    (3, 22): "Đi bộ",
    (3, 24): "Chạy bộ",
    (3, 25): "Dã ngoại",
    (3, 26): "Đi xe đạp",
    (3, 27): "Thiên văn"
}


def find_key_recursively(data, target_key):

    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            elif isinstance(value, (dict, list)):
                result = find_key_recursively(value, target_key)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = find_key_recursively(item, target_key)
            if result is not None:
                return result
    return None


def main():

    # --- Bước 1: Lấy dữ liệu ---
    print(f"Đang thử lấy dữ liệu mới từ: {URL}")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        redux_script = soup.find('script', {'id': 'redux-data'})

        if redux_script:
            print("Lấy dữ liệu mới thành công!")
            json_data = json.loads(redux_script.string)
            with open(RAW_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"Đã cập nhật file: {RAW_DATA_FILE}")
        else:
            print("Lấy dữ liệu mới thất bại. Sẽ thử dùng file đã có nếu tồn tại.")
            if not os.path.exists(RAW_DATA_FILE):
                print(f"Lỗi: File '{RAW_DATA_FILE}' không tồn tại. Không thể tiếp tục.")
                return
            with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu: {e}. Sẽ thử dùng file đã có nếu tồn tại.")
        if not os.path.exists(RAW_DATA_FILE):
            print(f"Lỗi: File '{RAW_DATA_FILE}' không tồn tại. Không thể tiếp tục.")
            return
        with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

    # --- Bước 2: Trích xuất ---
    print(f"\n--- BẮT ĐẦU TRÍCH XUẤT HOẠT ĐỘNG TỪ {RAW_DATA_FILE} ---")
    life_activity_data = find_key_recursively(json_data, 'lifeActivityData')

    if life_activity_data:
        print("Đã tìm thấy khối 'lifeActivityData'!")
        days_data = life_activity_data.get('days')

        if days_data and isinstance(days_data, list) and len(days_data) > 0:
            today_indices = days_data[0].get('lifeDailyIndices')

            if today_indices and isinstance(today_indices, list):
                extracted_activities = []
                for item in today_indices:
                    item_type = item.get("type")
                    item_sub_type = item.get("subType")
                    activity_name = ACTIVITY_MAP.get((item_type, item_sub_type), "Không xác định")

                    extracted_activities.append({
                        "name": activity_name,
                        "type": item_type,
                        "subType": item_sub_type,
                        "summary": item.get("summary"),
                        "taskbarSummary": item.get("taskbarSummary")
                    })

                with open(ACTIVITIES_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(extracted_activities, f, ensure_ascii=False, indent=2)

                print(f"Đã trích xuất và lưu {len(extracted_activities)} hoạt động vào file: {ACTIVITIES_OUTPUT_FILE}")
                print("\nHoàn tất! Kiểm tra file activities.json để xem kết quả.")
            else:
                print("Không tìm thấy 'lifeDailyIndices' trong ngày đầu tiên.")
        else:
            print("Không tìm thấy dữ liệu 'days' trong 'lifeActivityData'.")
    else:
        print("Không tìm thấy khối 'lifeActivityData' trong file JSON.")


if __name__ == "__main__":
    main()
