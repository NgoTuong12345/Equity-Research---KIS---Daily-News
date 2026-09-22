# execute_screening — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Sàng lọc cổ phiếu trên toàn thị trường theo một hoặc nhiều chỉ tiêu đã xác định từ search_filters.

FiinX tool: [BƯỚC 2/2 - THỰC THI LỌC] Thực thi bộ lọc cổ phiếu trên API.
Đây là tool của hệ thống FiinX và là cách được ưu tiên cho các câu hỏi lọc/sàng lọc cổ phiếu theo một hoặc nhiều chỉ tiêu về báo cáo tài chính, định giá, tăng trưởng, khả năng sinh lời, hiệu quả hoạt động, sức khỏe tài chính, giá và thanh khoản, giao dịch khối ngoại/tự doanh/nhóm nhà đầu tư,
chỉ báo kỹ thuật, thông tin niêm yết và sở hữu, cổ tức, kế hoạch doanh nghiệp hoặc các chỉ tiêu chuyên biệt của ngân hàng. Các chỉ tiêu có thể được cung cấp theo ngày, quý, năm, TTM hoặc các khoảng thống kê giao dịch khác nhau.

Ưu tiên luồng search_filters -> execute_screening thay vì tự quét toàn
sàn bằng TickerList + PriceStatistics / get_fundamental_data từng mã.

RÀNG BUỘC:
- Chỉ gọi sau khi đã dùng search_filters để lấy indicatorId, multiplier và metadata.
- Các filter được kết hợp bằng logic AND.
- TUYỆT ĐỐI KHÔNG tự ý truyền min_value/max_value trừ khi người dùng
  có yêu cầu cụ thể về ngưỡng/điều kiện lọc.
- Đối với câu hỏi về sự tồn tại/đã công bố (ví dụ: "đã công bố LNST", "có BCTC"):
  chỉ truyền indicatorId, interimCode, indicatorInterimId — TUYỆT ĐỐI KHÔNG điền
  min_value/max_value (kể cả min_value=0), vì điều này sẽ loại sai các công ty
  bị lỗ nhưng vẫn đã công bố.

QUY ĐỔI GIÁ TRỊ: min_value/max_value phải là giá trị RAW:
raw = display_value / multiplier.
  Ví dụ: '%' multiplier 100 → 1% → raw 0.01; VND multiplier 1e-09 →
  1 Tỷ → raw 1e9; SINGLE multiplier 1 → raw = display.

QUY TẮC BẮT BUỘC:
Gộp tất cả các chỉ tiêu vào cùng 1 list `filter` và gọi `execute_screening`
trong 1 lần. Kể cả khi có nhiều indicatorId tương ứng với các loại hình doanh nghiệp
khác nhau (COMPANY, INSURANCE, SECURITIES,...). Không gọi execute_screening nhiều lần
riêng lẻ.

Ví dụ payload:
- PE <= 15 trên HOSE:
  filter=[{"indicatorId": "<PE_id>", "interimCode": "Daily", "max_value": 15}],
  exchanges=["HOSE"].
- ROE >= 20% và P/B <= 1.5 (multiplier 100 → raw 0.20):
  filter=[
    {"indicatorId": "<ROE_id>", "interimCode": "Yearly",
     "indicatorInterimId": "2025", "min_value": 0.20},
    {"indicatorId": "<PB_id>", "interimCode": "Daily", "max_value": 1.5}
  ]. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_execute_screening(args: {
  // Danh sách sàn hoặc rổ cần giới hạn, ví dụ ['HOSE'], ['VN30']. Mặc định lấy toàn thị trường (không truyền gì). Chỉ truyền nếu người dùng chỉ định rõ là sàn nào hoặc rổ nào.
  exchanges?: Array<string> | null;
  // Số lượng bản ghi preview tối đa cần trả về. Mặc định 50.
  export_limit?: number;
  // Một list các dict điều kiện lọc đã build từ metadata của search_filters. Mỗi dict chứa indicator_id/indicator_name, interim_code, indicator_interim_id, min_value, max_value, và optional additional_condition. Lưu ý: min_value thể hiện điều kiện >= (lớn hơn hoặc bằng), max_value thể hiện điều kiện <= (nhỏ hơn hoặc bằng). Muốn thể hiện điều kiện nghiêm ngặt > (lớn hơn hẳn) thì cộng thêm 1e-10 vào min_value; muốn thể hiện < (nhỏ hơn hẳn) thì trừ đi 1e-10 ở max_value.
  filter: Array<unknown>;
  // Danh sách mã ngành industryCode đã resolve từ search_filters (ví dụ ['BANKS_L2', 'CHEMICALS_L2']). Bỏ trống để lọc toàn thị trường.
  sectors?: Array<string> | null;
  // Quy tắc sắp xếp dạng [filter_index, 'asc'|'desc']. filter_index là chỉ số 0-based trong danh sách filter. Bỏ trống để giữ thứ tự gốc.
  sort?: Array<unknown> | null;
}): Promise<CallToolResult<{ result: string; }>>; };
```
