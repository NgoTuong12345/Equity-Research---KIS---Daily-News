# report_mcp_bug — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Ghi nhận lỗi hệ thống MCP hoặc API còn thiếu để kỹ sư điều tra.

[BUG REPORT] FiinX MCP support tool: ghi nhận lỗi MCP hoặc thiếu API để kỹ sư điều tra.

RÀNG BUỘC CHO AI:
- Chỉ gọi tool này khi người dùng yêu cầu rõ ràng việc log/báo lỗi.
- Không tự động gọi nếu user chưa yêu cầu.
- Server tự gắn execution context; cung cấp `code`, `error_message` và
  `note` để lưu đủ ngữ cảnh debug. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_report_mcp_bug(args: {
  // Đoạn mã Python đã gây lỗi trong sandbox, nếu có.
  code?: string;
  // Thông báo lỗi chi tiết hoặc mô tả loại sự cố cần log.
  error_message?: string;
  // Ghi chú bổ sung: các thử nghiệm đã làm, từ khóa đã search, hoặc gợi ý fix.
  note?: string;
}): Promise<CallToolResult<{ result: string; }>>; };
```
