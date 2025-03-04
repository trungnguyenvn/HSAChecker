# HSA Exam Slot Checker - Hướng dẫn sử dụng

## Giới thiệu

Công cụ HSA Exam Slot Checker giúp bạn tự động kiểm tra và theo dõi các suất thi trống tại HSA một cách liên tục. Công cụ này chạy trực tiếp trong trình duyệt web của bạn và không yêu cầu cài đặt phần mềm bổ sung.

## Các bước sử dụng

### Bước 1: Đăng nhập vào trang web HSA

1. Mở trình duyệt (Chrome, Firefox, Edge...)
2. Truy cập vào trang web: https://id.hsa.edu.vn
3. Đăng nhập với tài khoản của bạn

### Bước 2: Mở Developer Tools (Công cụ nhà phát triển)

**Windows/Linux:**
- Nhấn phím `F12` hoặc
- Nhấn tổ hợp phím `Ctrl + Shift + I` hoặc
- Nhấp chuột phải vào trang web và chọn "Kiểm tra" (Inspect)

**MacOS:**
- Nhấn tổ hợp phím `Cmd + Option + I` hoặc
- Nhấp chuột phải vào trang web và chọn "Kiểm tra" (Inspect)

### Bước 3: Chọn tab Console

Trong cửa sổ Developer Tools vừa mở, chọn tab "Console" để chuẩn bị nhập mã.

### Bước 4: Sao chép và dán mã JavaScript

Sao chép toàn bộ đoạn mã dưới đây và dán vào tab Console:

```javascript
// HSA Exam Slot Checker cho trình duyệt - Phiên bản tiếng Việt
class HSAChecker {
  constructor() {
    // Cấu hình mặc định
    this.interval = 300; // giây giữa các lần kiểm tra
    this.delay = 2; // giây giữa các cuộc gọi API
    this.verbose = true;
    this.checkAllBatches = false;
    this.batchStatus = "OPENING";
    this.locationId = null;
    this.batchCode = null;
    this.resultsLog = [];
    this.availableFound = false;

    // Biến sẽ được thiết lập sau
    this.periodId = null;
    this.batchId = null;
    this.batchName = null;
    
    // Lấy token xác thực từ localStorage nếu có
    this.token = this.checkToken();
  }

  // Hàm tạm dừng sử dụng Promise
  sleep(seconds) {
    return new Promise(resolve => setTimeout(resolve, seconds * 1000));
  }

  // Wrapper cho cuộc gọi API với xác thực
  async apiCall(url, method = 'GET', data = null) {
    try {
      const options = {
        method: method,
        headers: {
          'Accept': 'application/json, text/plain, */*',
          'Authorization': `Bearer ${this.token}`
        }
      };

      if (method.toUpperCase() === 'POST' && data) {
        options.body = JSON.stringify(data);
        options.headers['Content-Type'] = 'application/json';
      }

      const response = await fetch(url, options);
      if (!response.ok) {
        console.error(`Lỗi gọi API: ${response.status} ${response.statusText}`);
        return {};
      }
      return await response.json();
    } catch (e) {
      console.error(`Lỗi gọi API: ${e.message}`);
      return {};
    } finally {
      await this.sleep(this.delay); // Áp dụng độ trễ sau mỗi lần gọi API
    }
  }

  // Helper tạo timestamp
  timestamp() {
    return new Date().toISOString().replace('T', ' ').substr(0, 19);
  }

  // Ghi log ra console
  log(message, forceDisplay = false) {
    const timestamp = this.timestamp();
    const fullMessage = message.startsWith(timestamp) ? message : `${timestamp} ${message}`;
    
    // Luôn ghi vào mảng kết quả
    this.resultsLog.push(fullMessage);
    
    // Chỉ ghi ra console nếu verbose = true hoặc forceDisplay = true
    if (this.verbose || forceDisplay) {
      console.log(fullMessage);
    }
  }

  // Các hàm API
  async fetchPeriods() {
    return await this.apiCall("https://api.hsa.edu.vn/exam/views/registration/available-period");
  }

  async fetchBatches(periodId) {
    return await this.apiCall(`https://api.hsa.edu.vn/exam/views/registration/available-batch?periodId=${periodId}`);
  }

  async fetchLocations(batchId) {
    return await this.apiCall(`https://api.hsa.edu.vn/exam/views/registration/available-location?batchId=${batchId}`);
  }

  // Kiểm tra các suất thi có sẵn cho một địa điểm
  async checkSlots(locationId, locationName, batchName = null, batchCode = null) {
    const response = await this.apiCall(`https://api.hsa.edu.vn/exam/views/registration/available-slot?locationId=${locationId}`);
    if (!response || !Array.isArray(response)) {
      this.log(`× Không thể lấy thông tin suất thi cho ${locationName} (ID: ${locationId})`);
      return false;
    }
    
    // Đếm số suất thi còn trống
    let availableCount = 0;
    const availableSlots = [];
    
    for (const slot of response) {
      const slotId = String(slot.id || '');
      const name = slot.name || 'Không rõ';
      const total = parseInt(slot.numberOfSeats || 0);
      const registered = parseInt(slot.registeredSlots || 0);
      const available = total - registered;
      
      if (available > 0) {
        availableCount++;
        const batchPrefix = batchCode ? `[${batchCode}] ` : '';
        const slotInfo = `${this.timestamp()} → ${batchPrefix}${name} (ID: ${slotId}): ${available}/${total} chỗ trống`;
        availableSlots.push(slotInfo);
      }
    }
    
    // Hiển thị kết quả
    const batchInfo = batchName && batchCode ? ` cho ${batchName} (Mã: ${batchCode})` : '';
    
    if (availableCount === 0) {
      if (this.verbose) {
        this.log(`× Không có suất thi nào trống tại ${locationName} (ID: ${locationId})${batchInfo}`);
      }
      return false;
    } else {
      this.log(`✓ ${locationName} (ID: ${locationId})${batchInfo} có ${availableCount} suất thi còn trống:`, true);
      for (const slot of availableSlots) {
        this.log(slot, true);
      }
      return true;
    }
  }

  // Chạy kiểm tra cho một đợt cụ thể
  async runCheckForBatch(batchId, batchName, batchCode) {
    this.log(`Bắt đầu kiểm tra cho Đợt: ${batchName} (Mã: ${batchCode}, ID: ${batchId})`, true);
    this.log("-------------------------------------------------------------------");
    
    let locationsWithSlots = 0;
    
    // Nếu locationId cụ thể được cung cấp
    if (this.locationId) {
      this.log(`Kiểm tra địa điểm cụ thể ID: ${this.locationId}`);
      
      // Lấy tên địa điểm trước
      const locationsResponse = await this.fetchLocations(batchId);
      let locationName = "Địa điểm không rõ";
      
      if (Array.isArray(locationsResponse)) {
        for (const loc of locationsResponse) {
          if (String(loc.id) === String(this.locationId)) {
            locationName = loc.name;
            break;
          }
        }
      }
      
      // Kiểm tra suất thi cho địa điểm này
      locationsWithSlots = (await this.checkSlots(this.locationId, locationName, batchName, batchCode)) ? 1 : 0;
    } else {
      // Lấy tất cả các địa điểm
      const locationsResponse = await this.fetchLocations(batchId);
      if (!locationsResponse || !Array.isArray(locationsResponse) || locationsResponse.length === 0) {
        this.log(`Lỗi: Không thể lấy danh sách địa điểm cho đợt ${batchCode} hoặc danh sách trống`);
        return false;
      }
      
      // Xử lý từng địa điểm
      let locationCount = 0;
      locationsWithSlots = 0;
      this.log(`Đang xử lý tất cả địa điểm trong đợt ${batchCode}...`);
      
      const totalLocations = locationsResponse.length;
      for (const location of locationsResponse) {
        const locationId = location.id;
        const locationName = location.name;
        locationCount++;
        
        // Hiển thị tiến trình
        console.log(`Đang kiểm tra địa điểm ${locationCount}/${totalLocations}: ${locationName}...`);
        
        // Kiểm tra suất thi
        if (await this.checkSlots(locationId, locationName, batchName, batchCode)) {
          locationsWithSlots++;
        }
      }
      
      // Hiển thị tổng kết cho đợt
      this.log(`--------------------------------------------------------------------`);
      this.log(`Đợt: ${batchName} (Mã: ${batchCode})`, true);
      this.log(`Tổng số địa điểm đã kiểm tra: ${locationCount}`, true);
      this.log(`Số địa điểm có suất thi trống: ${locationsWithSlots}`, true);
      this.log(`--------------------------------------------------------------------`);
    }
    
    // Trả về có tìm thấy suất trống hay không
    return locationsWithSlots > 0;
  }

  // Hiển thị các đợt thi có sẵn
  displayBatches(periodId, batches) {
    console.log("=====================================================================");
    console.log("CÁC ĐỢT THI HIỆN CÓ:");
    console.log("=====================================================================");
    
    if (Array.isArray(batches)) {
      for (const batch of batches) {
        const code = batch.code || 'N/A';
        const batchId = batch.id || 'N/A';
        const name = batch.name || 'N/A';
        const status = batch.status || 'N/A';
        const config = batch.config || {};
        const startDate = config.startDate || 'N/A';
        const endDate = config.endDate || 'N/A';
        const regEnd = config.registrationEndDateTime || 'N/A';
        
        console.log(`Mã: ${code} | ID: ${batchId} | Tên: ${name} | Trạng thái: ${status} | Bắt đầu: ${startDate} | Kết thúc: ${endDate} | Hết hạn đăng ký: ${regEnd}`);
      }
    } else {
      console.log("Không có đợt thi nào hoặc có lỗi khi lấy dữ liệu");
    }
    
    console.log("=====================================================================");
  }

  // Hàm kiểm tra chính
  async runCheck() {
    this.log("===================================================================", true);
    this.log("BẮT ĐẦU KIỂM TRA SUẤT THI", true);
    this.log("===================================================================", true);
    
    if (!this.token) {
      this.log("Lỗi: Không tìm thấy token xác thực. Vui lòng đăng nhập trước.", true);
      return false;
    }
    
    if (this.checkAllBatches) {
      // Lấy tất cả các đợt phù hợp
      const batchesResponse = await this.fetchBatches(this.periodId);
      
      if (!Array.isArray(batchesResponse)) {
        this.log("Lỗi: Không thể lấy danh sách đợt thi", true);
        return false;
      }
      
      const matchingBatches = batchesResponse.filter(b => b.status === this.batchStatus);
      
      if (!matchingBatches || matchingBatches.length === 0) {
        this.log(`Không tìm thấy đợt thi nào có trạng thái '${this.batchStatus}'.`, true);
        return false;
      }
      
      this.log(`Đang kiểm tra ${matchingBatches.length} đợt thi có trạng thái '${this.batchStatus}'`, true);
      
      // Theo dõi kết quả tổng thể
      let totalBatchesChecked = 0;
      let batchesWithSlots = 0;
      this.availableFound = false;
      
      // Kiểm tra từng đợt
      for (const batch of matchingBatches) {
        const batchId = batch.id;
        const batchName = batch.name;
        const batchCode = batch.code;
        totalBatchesChecked++;
        
        // Chạy kiểm tra cho đợt này
        if (await this.runCheckForBatch(batchId, batchName, batchCode)) {
          batchesWithSlots++;
          this.availableFound = true;
        }
        
        // Thêm dòng phân cách giữa các đợt
        this.log("-------------------------------------------------------------------");
      }
      
      // Hiển thị kết quả cuối cùng
      this.log("====================================================================", true);
      this.log("TỔNG KẾT KẾT QUẢ:", true);
      this.log("====================================================================", true);
      this.log(`Tổng số đợt đã kiểm tra: ${totalBatchesChecked}`, true);
      this.log(`Số đợt có suất thi trống: ${batchesWithSlots}`, true);
      this.log("--------------------------------------------------------------------", true);
      
      // Báo cáo nếu tìm thấy suất trống trong bất kỳ đợt nào
      if (this.availableFound) {
        this.log("ĐÃ TÌM THẤY SUẤT THI TRỐNG! Kiểm tra log để xem chi tiết.", true);
      } else {
        this.log("Không tìm thấy suất thi trống trong bất kỳ đợt nào.", true);
      }
    } else {
      // Sử dụng đợt duy nhất đã được xác định
      if (!this.batchId) {
        this.log("Lỗi: Không có đợt nào được chọn. Chạy thiết lập trước.", true);
        return false;
      }
      
      this.availableFound = await this.runCheckForBatch(this.batchId, this.batchName, this.batchCode);
      
      // Hiển thị kết quả
      if (this.availableFound) {
        this.log("ĐÃ TÌM THẤY SUẤT THI TRỐNG! Xem phía trên để biết chi tiết.", true);
      } else {
        this.log("Không tìm thấy suất thi trống.", true);
      }
    }
    
    this.log("====================================================================", true);
    this.log(`Đã hoàn thành kiểm tra lúc ${new Date().toLocaleString('vi-VN')}`, true);
    
    return this.availableFound;
  }

  // Phương thức thực thi chính
  async run() {
    console.clear();
    console.log("HSA Exam Slot Checker - Phiên bản tiếng Việt");
    console.log(`Sử dụng độ trễ API: ${this.delay} giây`);
    
    if (!this.token) {
      console.error("Lỗi: Không tìm thấy token xác thực trong localStorage.");
      console.error("Vui lòng đảm bảo bạn đã đăng nhập vào trang web HSA.");
      this.showTokenGuide();
      return false;
    }
    
    try {
      // Lấy danh sách kỳ thi hiện có
      console.log("Đang lấy thông tin kỳ thi...");
      const periodsResponse = await this.fetchPeriods();
      
      if (!periodsResponse || !Array.isArray(periodsResponse) || periodsResponse.length === 0) {
        console.error("Lỗi: Không tìm thấy kỳ thi nào đang hoạt động.");
        console.error("Token có thể đã hết hạn, vui lòng thử lấy token mới.");
        this.showTokenGuide();
        return false;
      }
      
      // Lấy ID kỳ thi đầu tiên
      this.periodId = periodsResponse[0].id;
      console.log(`Đã tìm thấy kỳ thi ID: ${this.periodId}`);
      
      // Lấy danh sách các đợt thi
      const batchesResponse = await this.fetchBatches(this.periodId);
      
      // Hiển thị tất cả các đợt
      this.displayBatches(this.periodId, batchesResponse);
      
      if (!Array.isArray(batchesResponse)) {
        console.error("Lỗi: Không thể lấy danh sách đợt thi");
        return false;
      }
      
      // Nếu không kiểm tra tất cả đợt, lấy thông tin đợt cụ thể
      if (!this.checkAllBatches) {
        // Trích xuất thông tin đợt thi
        if (this.batchCode) {
          // Tìm đợt cụ thể theo mã
          let batchFound = false;
          for (const batch of batchesResponse) {
            if (batch.code === this.batchCode) {
              this.batchId = batch.id;
              this.batchName = batch.name;
              const batchStatus = batch.status;
              batchFound = true;
              break;
            }
          }
          
          if (!batchFound) {
            console.error(`Lỗi: Không tìm thấy mã đợt '${this.batchCode}'.`);
            return false;
          }
        } else {
          // Tìm đợt OPENING đầu tiên
          const openingBatches = batchesResponse.filter(b => b.status === "OPENING");
          
          if (!openingBatches || openingBatches.length === 0) {
            console.error("Lỗi: Không tìm thấy đợt thi nào đang mở.");
            return false;
          }
          
          const batch = openingBatches[0];
          this.batchId = batch.id;
          this.batchName = batch.name;
          this.batchCode = batch.code;
        }
        
        console.log(`Sử dụng đợt: ${this.batchName} (Mã: ${this.batchCode}, ID: ${this.batchId})`);
      } else {
        console.log("Sẽ kiểm tra TẤT CẢ các đợt có trạng thái:", this.batchStatus);
      }
      
      // Chạy kiểm tra
      return await this.runCheck();
    } catch (error) {
      console.error("Có lỗi xảy ra:", error);
      return false;
    }
  }
  
  // Hàm giám sát liên tục
  async startMonitoring() {
    if (!this.token) {
      console.error("Lỗi: Không tìm thấy token xác thực trong localStorage.");
      console.error("Vui lòng đảm bảo bạn đã đăng nhập vào trang web HSA.");
      this.showTokenGuide();
      return false;
    }
    
    let runCount = 0;
    
    try {
      // Thiết lập ban đầu - lấy thông tin kỳ thi và đợt thi
      console.log("Đang thiết lập chế độ giám sát...");
      const periodsResponse = await this.fetchPeriods();
      
      if (!periodsResponse || !Array.isArray(periodsResponse) || periodsResponse.length === 0) {
        console.error("Lỗi: Không tìm thấy kỳ thi nào đang hoạt động.");
        return false;
      }
      
      // Lấy ID kỳ thi đầu tiên
      this.periodId = periodsResponse[0].id;
      console.log(`Đã tìm thấy kỳ thi ID: ${this.periodId}`);
      
      // Lấy danh sách các đợt thi
      const batchesResponse = await this.fetchBatches(this.periodId);
      
      if (!Array.isArray(batchesResponse)) {
        console.error("Lỗi: Không thể lấy danh sách đợt thi");
        return false;
      }
      
      // Nếu không kiểm tra tất cả đợt, lấy thông tin đợt cụ thể
      if (!this.checkAllBatches) {
        if (this.batchCode) {
          // Tìm đợt cụ thể theo mã
          let batchFound = false;
          for (const batch of batchesResponse) {
            if (batch.code === this.batchCode) {
              this.batchId = batch.id;
              this.batchName = batch.name;
              batchFound = true;
              break;
            }
          }
          
          if (!batchFound) {
            console.error(`Lỗi: Không tìm thấy mã đợt '${this.batchCode}'.`);
            return false;
          }
        } else {
          // Tìm đợt OPENING đầu tiên
          const openingBatches = batchesResponse.filter(b => b.status === "OPENING");
          
          if (!openingBatches || openingBatches.length === 0) {
            console.error("Lỗi: Không tìm thấy đợt thi nào đang mở.");
            return false;
          }
          
          const batch = openingBatches[0];
          this.batchId = batch.id;
          this.batchName = batch.name;
          this.batchCode = batch.code;
        }
        
        console.log(`Sử dụng đợt: ${this.batchName} (Mã: ${this.batchCode}, ID: ${this.batchId})`);
      } else {
        console.log("Sẽ kiểm tra TẤT CẢ các đợt có trạng thái:", this.batchStatus);
      }
      
      // Bắt đầu vòng lặp giám sát
      while (true) {
        runCount++;
        console.log(`Lần kiểm tra #${runCount} lúc ${new Date().toLocaleString('vi-VN')}`);
        await this.runCheck();
        console.log(`Lần kiểm tra tiếp theo trong ${this.interval} giây.`);
        
        // Chờ đến lần kiểm tra tiếp theo
        await this.sleep(this.interval);
      }
    } catch (error) {
      console.error("Có lỗi xảy ra trong quá trình giám sát:", error);
      return false;
    }
  }
  
  // Cấu hình trình kiểm tra
  configure(options = {}) {
    if (options.batchCode !== undefined) this.batchCode = options.batchCode;
    if (options.locationId !== undefined) this.locationId = options.locationId;
    if (options.interval !== undefined) this.interval = options.interval;
    if (options.delay !== undefined) this.delay = options.delay;
    if (options.verbose !== undefined) this.verbose = options.verbose;
    if (options.checkAllBatches !== undefined) this.checkAllBatches = options.checkAllBatches;
    if (options.batchStatus !== undefined) this.batchStatus = options.batchStatus;
    if (options.token !== undefined) this.token = options.token;
    
    return this;
  }
  
  // Trích xuất token từ localStorage và kiểm tra tính hợp lệ
  checkToken() {
    // Thử lấy token
    let token = localStorage.getItem('token');
    
    if (!token) {
      // Nếu không tìm thấy trong localStorage thông thường, kiểm tra các vị trí lưu trữ token khác
      const appState = localStorage.getItem('appState');
      if (appState) {
        try {
          const parsedState = JSON.parse(appState);
          if (parsedState.auth && parsedState.auth.token) {
            token = parsedState.auth.token;
            console.log("Đã tìm thấy token trong appState");
          }
        } catch (e) {
          console.error("Lỗi khi phân tích cú pháp appState từ localStorage:", e);
        }
      }
      
      // Kiểm tra các vị trí lưu trữ token tiềm năng khác
      if (!token) {
        const hsa_token = localStorage.getItem('hsa_token');
        if (hsa_token) {
          token = hsa_token;
          console.log("Đã tìm thấy token trong hsa_token");
        }
      }
    } else {
      console.log("Đã tìm thấy token trong localStorage");
    }
    
    return token;
  }
  
  // Hiển thị hướng dẫn lấy token
  showTokenGuide() {
    console.log("\n=================================================================");
    console.log("HƯỚNG DẪN LẤY TOKEN XÁC THỰC");
    console.log("=================================================================");
    console.log("Cách 1: Lấy từ Network Tab trong Developer Tools");
    console.log("-----------------------------------------------------------------");
    console.log("1. Đăng nhập vào trang web HSA (https://id.hsa.edu.vn)");
    console.log("2. Mở Developer Tools (F12 hoặc Chuột phải > Inspect)");
    console.log("3. Chọn tab Network");
    console.log("4. Tải lại trang (F5)");
    console.log("5. Tìm bất kỳ request nào đến api.hsa.edu.vn");
    console.log("6. Kiểm tra Headers > Request Headers > Authorization");
    console.log("7. Sao chép phần sau 'Bearer ' (không bao gồm từ 'Bearer')");
    console.log("\nCách 2: Lấy từ Local Storage");
    console.log("-----------------------------------------------------------------");
    console.log("1. Đăng nhập vào trang web HSA (https://id.hsa.edu.vn)");
    console.log("2. Mở Developer Tools (F12 hoặc Chuột phải > Inspect)");
    console.log("3. Chọn tab Application > Local Storage > https://id.hsa.edu.vn");
    console.log("4. Tìm khóa 'token' hoặc 'appState' và sao chép giá trị");
    console.log("   - Nếu là 'appState', bạn cần trích xuất token từ JSON");
    console.log("\nSau khi lấy được token, chạy lệnh sau:");
    console.log('hsaChecker.configure({token: "token-của-bạn", interval: 300}).startMonitoring()');
    console.log("=================================================================\n");
  }
}

// Tạo một thể hiện mới và chạy trình kiểm tra
const hsaChecker = new HSAChecker();

// Hiển thị hướng dẫn lấy token
hsaChecker.showTokenGuide();

// Hướng dẫn sử dụng
console.log("HSA Exam Slot Checker - Phiên bản tiếng Việt");
console.log("-----------------------------------");
console.log("1. Để chạy một lần với cài đặt mặc định:");
console.log("   hsaChecker.run()");
console.log("");
console.log("2. Để cấu hình tùy chọn trước:");
console.log("   hsaChecker.configure({");
console.log("     batchCode: '123',      // Tùy chọn: Kiểm tra mã đợt thi cụ thể");
console.log("     locationId: '456',     // Tùy chọn: Kiểm tra địa điểm cụ thể");
console.log("     interval: 300,         // Giây giữa các lần kiểm tra trong chế độ giám sát");
console.log("     delay: 2,              // Giây giữa các cuộc gọi API");
console.log("     verbose: true,         // Hiển thị đầu ra chi tiết");
console.log("     checkAllBatches: false // Kiểm tra tất cả các đợt hay không");
console.log("   }).run()");
console.log("");
console.log("3. Để bắt đầu chế độ giám sát (sẽ chạy lặp lại):");
console.log("   hsaChecker.configure({interval: 300}).startMonitoring()");
console.log("");
console.log("4. Để dừng giám sát, tải lại trang hoặc đóng tab.");
```

### Bước 5: Nhấn Enter để chạy mã

Sau khi dán xong, nhấn phím `Enter` để thực thi mã. Hệ thống sẽ hiển thị hướng dẫn cách sử dụng công cụ.

### Bước 6: Kiểm tra token xác thực

Công cụ sẽ tự động tìm kiếm token xác thực trong trình duyệt của bạn. Nếu bạn đã đăng nhập thành công vào trang HSA, token sẽ được tìm thấy tự động. Nếu không tìm thấy, bạn cần lấy token thủ công:

**Lấy token từ Network tab**

1. Trong cửa sổ Developer Tools, chọn tab "Network"
2. Tải lại trang web (F5)
3. Tìm bất kỳ request nào đến `sign-in`
4. Nhấp vào request đó
5. Chọn tab "Reponse"
6. Tìm dòng "token"
7. Sao chép phần token trong ""
   
### Bước 7: Chạy công cụ

Có nhiều cách để chạy công cụ tùy theo nhu cầu của bạn:

**Cung cấp token thủ công:**
```javascript
hsaChecker.configure({token: "token-của-bạn", interval: 120, checkAllBatches: true}).startMonitoring()
```

**Để chạy kiểm tra một lần:**
```javascript
hsaChecker.run()
```

**Để theo dõi suất thi liên tục (mỗi 5 phút):**
```javascript
hsaChecker.configure({interval: 300}).startMonitoring()
```

**Để kiểm tra một đợt thi cụ thể:**
```javascript
hsaChecker.configure({batchCode: "502"}).run()
```

**Để kiểm tra tất cả các đợt thi đang mở:**
```javascript
hsaChecker.configure({checkAllBatches: true}).run()
```

**Để kiểm tra một địa điểm cụ thể:**
```javascript
hsaChecker.configure({locationId: "123"}).run()
```

### Bước 8: Đọc kết quả

Công cụ sẽ hiển thị kết quả kiểm tra trong console. Nếu tìm thấy suất thi trống, thông báo sẽ được hiển thị với chi tiết về địa điểm và số chỗ trống có sẵn.

### Bước 9: Dừng công cụ

Để dừng công cụ đang chạy ở chế độ giám sát:
- Tải lại trang web, hoặc
- Đóng tab trình duyệt, hoặc
- Nhấn tổ hợp phím `Ctrl+C` trong console (một số trình duyệt hỗ trợ)

## Lưu ý quan trọng

1. **Bạn phải đăng nhập vào trang HSA trước** khi chạy công cụ
2. **Không đóng tab trình duyệt** khi đang chạy chế độ giám sát
3. **Không tải lại trang** nếu muốn tiếp tục giám sát
4. Nếu token hết hạn, bạn cần đăng nhập lại và lấy token mới

## Các tùy chọn cấu hình

| Tùy chọn | Mô tả | Giá trị mặc định |
|----------|-------|-----------------|
| `batchCode` | Mã đợt thi cần kiểm tra | Đợt OPENING đầu tiên |
| `locationId` | ID địa điểm cần kiểm tra | Tất cả địa điểm |
| `interval` | Thời gian giữa các lần kiểm tra (giây) | 300 |
| `delay` | Độ trễ giữa các cuộc gọi API (giây) | 2 |
| `verbose` | Hiển thị thông tin chi tiết | true |
| `checkAllBatches` | Kiểm tra tất cả các đợt | false |
| `token` | Token xác thực thủ công | null |

## Hỗ trợ

Nếu gặp vấn đề khi sử dụng công cụ, hãy thử các bước sau:

1. Đảm bảo bạn đã đăng nhập vào trang HSA trước khi chạy công cụ
2. Kiểm tra console để xem thông báo lỗi
3. Thử lấy token thủ công và cung cấp qua tùy chọn `token`
4. Làm mới trang và thử lại

---

Chúc bạn tìm được suất thi phù hợp! 🎓
