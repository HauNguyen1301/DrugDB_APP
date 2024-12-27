import requests
import pandas as pd
import time
from datetime import datetime

def scrape_services_api(limit=None):
    """
    Crawl dữ liệu từ API
    Args:
        limit (int, optional): Số lượng record muốn lấy. Nếu None sẽ lấy tất cả dữ liệu.
    """
    api_url = "https://dichvucong.dav.gov.vn/api/services/app/SoDangKy/GetAllPublicServerPaging"
    
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
    }
    
    all_data = []
    skip_count = 0
    max_results = 15  # Số lượng kết quả mỗi lần request
    total_count = None
    
    while True:
        try:
            payload = {
                "filterText": "",  # Bỏ filter bromhexin
                "SoDangKyThuoc": {},
                "KichHoat": None,  # Set về None để lấy tất cả status
                "skipCount": skip_count,
                "maxResultCount": max_results,
                "sorting": None
            }
            
            # Hiển thị tiến trình
            if total_count:                
                timestamp = datetime.now().strftime("%d/%m/%Y_%H:%M:%S")
                print(f"\nĐang lấy dữ liệu: {len(all_data)}/{total_count} records - at {timestamp}")
            else:
                print(f"\nĐang lấy dữ liệu từ vị trí {skip_count}...")
            
            if limit:
                print(f"Đã lấy được: {len(all_data)}/{limit} records")
            
            # Thực hiện POST request
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Lấy tổng số record nếu chưa có
            if total_count is None and 'result' in data:
                total_count = data['result'].get('totalCount', 0)
                print(f"Tổng số records có sẵn: {total_count}")
            
            # Kiểm tra và lấy dữ liệu
            if not data or 'result' not in data or not data['result'].get('items'):
                print("Không còn dữ liệu để lấy")
                break
            
            items = data['result']['items']
            
            if not items:
                break
            
            # Thêm dữ liệu vào list
            if limit:
                remaining = limit - len(all_data)
                items_to_add = items[:remaining]
                all_data.extend(items_to_add)
            else:
                all_data.extend(items)
            
            print(f"Đã lấy thêm {len(items)} records")
            
            # Kiểm tra điều kiện dừng
            if limit and len(all_data) >= limit:
                print(f"Đã đạt đủ {limit} records")
                break
                
            if not limit and total_count and len(all_data) >= total_count:
                print("Đã lấy hết tất cả dữ liệu")
                break
            
            skip_count += max_results
            time.sleep(1)  # Delay 1 giây giữa các request
            
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi request: {str(e)}")
            break
        except Exception as e:
            print(f"Lỗi không xác định: {str(e)}")
            import traceback
            print(traceback.format_exc())
            break
    
    if all_data:
        # Chuyển đổi sang DataFrame
        df = pd.DataFrame(all_data)
        
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if limit:
            output_file = f'public_services_sample_{timestamp}.csv'
        else:
            output_file = f'public_services_full_{timestamp}.csv'
        
        # Lưu file CSV
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nĐã lưu {len(all_data)} records vào file {output_file}")
        
        return df
    else:
        print("Không lấy được dữ liệu")
        return None

if __name__ == "__main__":
    print("Bắt đầu crawl dữ liệu...")
    result = scrape_services_api()  # Crawl toàn bộ dữ liệu
    if result is not None:
        print("\nMẫu dữ liệu đã crawl:")
        print(result.head())
        print(f"\nTổng số records đã lấy: {len(result)} - lúc: {timestamp}")