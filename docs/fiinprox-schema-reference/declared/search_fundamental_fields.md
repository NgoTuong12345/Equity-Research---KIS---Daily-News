# search_fundamental_fields — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Tìm chỉ tiêu báo cáo tài chính/tỷ số tài chính trước khi trích xuất bằng get_fundamental_data.

FiinX tool: tìm kiếm (Discovery) thông tin các chỉ tiêu trên Báo cáo tài chính và Chỉ số tài chính (Ratios).

Đây là tool dữ liệu cơ bản của hệ thống FiinX cho báo cáo tài chính và ratios doanh nghiệp Việt Nam.
Tool này trả về danh sách các kết quả phù hợp với từ khóa, bao gồm 'path_mapping', 'keyword', 'description', 'statement_type' và 'data_type'.
Không dùng tool này cho định giá/chỉ số thị trường theo thời gian của index/rổ như P/E, P/B của VNINDEX/VN30 trong 1 tháng; các câu đó phải quay về `search_tool_candidates` để chọn API thị trường phù hợp.
- 'data_type' và 'statement_type': Dùng các giá trị này để truyền trực tiếp vào tham số `data_type` và `statement` của tool `get_fundamental_data`.
- Lấy giá trị trong 'path_mapping' (là dict mapping giữa loại hình doanh nghiệp và field path, vd: {"BANK": "loans...", "COMPANY": "short_term..."}). Dựa vào loại hình doanh nghiệp của mã chứng khoán, chọn field path tương ứng để truyền vào tham số `fields` của tool `get_fundamental_data`. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_search_fundamental_fields(args: {
  // Từ khóa hoặc danh sách từ khóa chỉ tiêu báo cáo tài chính cần tìm. Ví dụ: 'hàng tồn kho' hoặc ['hàng tồn kho', 'lợi nhuận gộp'].
  searching_keywords: string | Array<string>;
  // Số lượng kết quả trả về cho mỗi truy vấn. Mặc định là 5.
  top_k?: number;
}): Promise<CallToolResult<{ result: string; }>>; };
```
