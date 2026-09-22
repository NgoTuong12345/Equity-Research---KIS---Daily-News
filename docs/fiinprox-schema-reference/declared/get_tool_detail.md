# get_tool_detail — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Xem chi tiết schema/tham số của tool đã được shortlist từ search_tool_candidates.

[BƯỚC 2 - SCHEMA & EXECUTION HINTS] Xem chi tiết tool đã shortlist.

Đây là tool schema/detail của hệ thống FiinX: đọc mô tả, tham số,
output description và execution hints của các API FiinX đã được shortlist.

NGỮ CẢNH SỬ DỤNG:
- Gọi sau `search_tool_candidates` để đọc schema, output description,
  usage instruction, wrapper nội bộ và execution rules của 1-2 tool đã chọn.

RÀNG BUỘC CHO AI:
- Bắt buộc dùng tool này trước khi viết code cho `execute_api`.
- Truyền tên hàm vào `func_name` hoặc id cache vào `tool_id`.
- Server tự nối execution flow và nạp wrapper/cache context của phiên hiện tại.
- Phải đọc kỹ tham số bắt buộc, format ngày tháng, wrapper requirements và
  execution rules trước khi viết code.

BƯỚC TIẾP THEO:
- Sau khi đã chọn đúng tool và hiểu schema, mới được viết mã Python để gọi
  `execute_api`.
- Output này vẫn chưa phải câu trả lời cuối. Nếu có tool usable, bắt buộc
  gọi `execute_api` để lấy dữ liệu/runtime output trước khi trả lời user. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_tool_detail(args: {
  // Metadata giám sát do client tự chèn; được chấp nhận để tránh lỗi validation và sẽ bị bỏ qua.
  ServerName?: string | null;
  agent_id?: string | null;
  // Mức chi tiết metadata trả về: `minimal`, `execution`, hoặc `full`. Mặc định `execution`.
  detail_level?: string;
  // Tên hàm đã chọn từ `function_candidates`. Dùng khi lấy detail cho tool thường.
  func_name?: string | Array<string> | null;
  // Biến thể truyền nhiều tên hàm; chỉ dùng khi cần xem detail cho nhiều tool đã shortlist.
  func_names?: string | Array<string> | null;
  // Metadata giám sát do client tự chèn; được chấp nhận để tránh lỗi validation và sẽ bị bỏ qua.
  toolAction?: string | null;
  // Metadata giám sát do client tự chèn; được chấp nhận để tránh lỗi validation và sẽ bị bỏ qua.
  toolSummary?: string | null;
  // ID cache đã chọn từ `cache_candidates`. Dùng thay cho `func_name` khi ưu tiên lời giải cache.
  tool_id?: string | Array<string> | null;
}): Promise<CallToolResult<{ [key: string]: unknown; }>>; };
```
