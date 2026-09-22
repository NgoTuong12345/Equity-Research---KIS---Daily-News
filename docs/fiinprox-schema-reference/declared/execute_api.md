# execute_api — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Thực thi mã Python gọi API đã chọn trong sandbox để lấy dữ liệu/tính toán chuyên sâu.

[BƯỚC 3 - SANDBOX EXECUTION] Thực thi mã Python gọi API trong sandbox.

Đây là bước thực thi API FiinX đã chọn từ `search_tool_candidates` và
`get_tool_detail`. Dữ liệu trả về thuộc hệ thống FiinX.

NGỮ CẢNH SỬ DỤNG:
- Dùng tool này sau khi đã đọc schema và execution hints từ `get_tool_detail`.
- Phù hợp để chạy code gọi các API domain-specific hoặc wrapper/cache function
  đã được shortlist ở các bước trước.

QUY TẮC VIẾT CODE CHO AI:
1. Dùng đối tượng `client` toàn cục đã có sẵn. KHÔNG import `FiinClient`,
   KHÔNG tạo `client = FiinClient()`.
2. Dùng đúng tham số và wrapper instructions lấy từ `get_tool_detail`.
3. Bắt buộc dùng `print()` để ghi kết quả ra stdout; nếu không in, response có thể rỗng.
4. Chỉ dùng các biến/thư viện đã được preload sẵn trong runtime, gồm:
   `client`, `pd`, `np`, `plt`, `mdates`, `datetime`, `timedelta`, `date`,
   `relativedelta`, `json`, `reduce`, `search_fundamental_fields`,
   `get_fundamental_data`, và các typing aliases cơ bản.
5. KHÔNG tự thêm helper introspection/dynamic access như `getattr`, `setattr`,
   `delattr`, `globals`, `locals`, `vars`, `eval`, `exec`, `__import__`.
   KHÔNG import các module hệ thống/network như `os`, `sys`, `subprocess`,
   `socket`, `urllib`, `requests`. Sandbox sẽ chặn các hàm/module này.
6. Ưu tiên truyền tham số trực tiếp và viết script ngắn, rõ ràng; tránh tạo abstraction,
   loop hoặc helper tiện ích không cần thiết nếu chỉ để gọi 1 API.
7. Nếu `get_tool_detail` đã cung cấp wrapper nội bộ thì chỉ gọi đúng hàm wrapper
   hoặc đúng method của `client`; không dựng thêm lớp/phương thức trung gian để
   truy cập động vào SDK.
8. KHÔNG dùng tool này để tự viết code truy vấn báo cáo tài chính hoặc ratios;
   các truy vấn đó phải dùng `search_fundamental_fields` -> `get_fundamental_data`.

XỬ LÝ KẾT QUẢ:
- usable: stdout có dữ liệu -> dùng để trả lời.
- empty: thử điều chỉnh tham số hoặc chọn tool khác.
- errored: sửa code/tham số và retry tối đa 1 lần.
- partial: nếu đã có một phần dữ liệu hữu ích thì trả lời phần đó. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_execute_api(args: {
  agent_id?: string | null;
  // CHUỖI MÃ NGUỒN PYTHON hoàn chỉnh để chạy trong sandbox. Phải tự viết lệnh gọi hàm hợp lệ, phải có `print()` để in kết quả ra stdout, và chỉ được dùng các biến/thư viện đã được preload sẵn thay vì tự tạo helper như `getattr` hoặc import thêm module hệ thống/network.
  code: string;
}): Promise<CallToolResult<{ result: string; }>>; };
```
