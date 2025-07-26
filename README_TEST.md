# Hướng dẫn kiểm tra lấy dữ liệu thời tiết

Script này giúp bạn kiểm tra việc lấy dữ liệu thời tiết từ dbtt.edu.vn trước khi tích hợp vào Home Assistant.

## Cài đặt các thư viện cần thiết

```
pip install -r requirements_test.txt
```

## Chạy script test

### Chạy với tham số mặc định (Hải Dương, Gia Lộc)

```
python test_weather_data.py
```

### Chạy với các tỉnh/huyện khác

```
python test_weather_data.py hai-duong gia-loc
python test_weather_data.py ha-noi hoan-kiem
python test_weather_data.py ho-chi-minh quan-1
```

**Lưu ý quan trọng**: Tham số phải sử dụng dấu gạch ngang ("-") chứ không phải dấu gạch dưới ("_").

## Kết quả

Script sẽ hiển thị:
- Thông tin thời tiết hiện tại (nhiệt độ, điều kiện, độ ẩm, gió, ...)
- Dự báo theo ngày (5 ngày tới)
- Dự báo theo giờ (hiển thị 5 mục đầu tiên)

Ngoài ra, script sẽ lưu toàn bộ dữ liệu vào file `weather_data.json` để bạn có thể phân tích chi tiết. 