# search_filters — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Tìm đúng chỉ tiêu (indicatorId) dùng để lọc cổ phiếu, dùng trước khi gọi execute_screening.

FiinX tool: [BƯỚC 1/2 - TÌM CHỈ TIÊU] Tìm field screening trước khi chạy lọc.

Dùng tool này khi user muốn sàng lọc cổ phiếu theo một hoặc nhiều điều kiện
như P/E, vốn hóa, tăng trưởng EPS, ROE, thanh khoản hoặc theo ngành.

Catalog screening có nhiều chỉ tiêu trùng phạm vi với FundamentalAnalysis
(BCKQKD, BCĐKT, LCTT, ROE, ROA...). Tuy nhiên KHÔNG truyền trực tiếp
fields/path_mapping của FundamentalAnalysis vào screening. Phải tìm
indicatorId riêng bằng search_filters.

LƯU Ý: Nếu người dùng hỏi về "kqkd" hoặc "kết quả kinh doanh", dùng
keyword "Lợi nhuận sau thuế", không nhầm với "Doanh thu".

Bộ indicator rất rộng: báo cáo tài chính, định giá, giao dịch khối
ngoại/tự doanh/cá nhân/tổ chức, chỉ báo kỹ thuật, cổ tức, kế hoạch
doanh nghiệp, chỉ tiêu ngân hàng... Ưu tiên tìm indicator qua tool
này rồi chạy execute_screening, thay vì quét thủ công bằng TickerList
+ PriceStatistics (chậm, dễ sai ngưỡng).

Output trả về: indicatorId, unit, multiplier, periods, path_mapping.

Sau bước này, dùng metadata để xây filter rồi gọi execute_screening.
Ưu tiên screening/batch thay vì quét từng mã riêng lẻ. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_search_filters(args: {
  // Danh sách từ khóa chỉ tiêu tài chính cần tìm, ví dụ ['ROE', 'P/E', 'Doanh thu thuần']. Dùng hybrid search (BM25 + dense) để tìm indicator phù hợp. Kết quả trả về indicatorsByQuery chứa các indicator riêng từng query, và sharedIndicators cho các indicator khớp nhiều query.
  indicator_keyword?: Array<string> | null;
  // Danh sách tên ngành/sector cần resolve mã ngành, ví dụ ['ngân hàng', 'bất động sản']. Kết quả trả về sectorsByQuery chứa industryCode dùng cho execute_screening.sectors.
  sector_keyword?: Array<string> | null;
  // Cấp phân ngành ICB (1-5) để giới hạn kết quả ngành. Bỏ trống để tìm tất cả các cấp. Dùng 2 khi hỏi ngành rộng, 4-5 khi cần ngành chi tiết.
  sector_level?: number | null;
  // Số kết quả tối đa cho mỗi sector query. Mặc định 10.
  sector_top_k?: number;
  // Số kết quả tối đa cho mỗi indicator query. Mặc định 10.
  top_k?: number;
}): Promise<CallToolResult<{ result: string; }>>; };
```
