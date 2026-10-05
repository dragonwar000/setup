---
type: draft
title: "R19 mở rộng — kết luận về code neo vào dòng, lời gọi hàm không tính là chứng cứ"
tags: [caveman, output-report, R19, evidence, code-line, sdk]
timestamp: 2026-09-08
---

# 080926-r19-code-line-sdk-warning
**Type:** draft
**Status:** proposed
**Tags:** caveman, output-report
**Proposed:** 2026-09-08

## What

Mở rộng R19 `evidence-terminal`: kết luận về code phải neo vào SỐ DÒNG trong mã nguồn, và dòng neo
không được chỉ là một LỜI GỌI HÀM — hàm có trong source thì phải trỏ tiếp tới dòng định nghĩa, hàm
nằm trong SDK/thư viện thì phải tra tài liệu SDK kèm CẢNH BÁO ĐỎ cho người đọc.

## Output

**Kind mới `code-line`** (điểm cuối thứ bảy). `evidence.ref` bắt buộc dạng `path/file.ext:LINE` hoặc
`:START-END`; validator mở đúng dòng đó ra đọc và phân loại:

- Dòng là định nghĩa / gán / thân logic → điểm cuối hợp lệ.
- Dòng **chỉ là lời gọi hàm** → chưa xong. Phải khai đúng một trong hai:
  - `impl_ref: "path:LINE"` — hàm có định nghĩa trong source. Validator kiểm dòng đó thật sự khai
    báo hàm ấy, không phải một lời gọi khác.
  - `sdk_doc: {url, accessed, quote}` — hàm nằm trong SDK/thư viện. Chịu đúng kỷ luật của `web`:
    url tuyệt đối trỏ đúng mục, ngày tra cứu, trích nguyên văn.
- Khai cả hai → lỗi. Khai `sdk_doc` cho hàm mà `git grep` tìm thấy định nghĩa trong repo → lỗi
  (đang đọc mô tả thay vì đọc code đang chạy).
- Nhiều lời gọi trên một dòng → bắt buộc khai `evidence.callee`, validator không đoán hộ.

**Cảnh báo đỏ hai chỗ.** Mỗi lá `sdk_doc` làm validator in một dòng ANSI đỏ lên terminal (in cả khi
chuỗi đã hợp lệ — đây là cảnh báo, không phải lỗi), VÀ tài liệu phải mang một dòng chứa
`🔴 CẢNH BÁO SDK`; thiếu dòng đó thì chuỗi bị chặn. So khớp bỏ dấu nên `CANH BAO SDK` cũng tính.
Lý do tách hai chỗ: cảnh báo terminal chỉ người chạy validator thấy, người đọc lại tài liệu sáu
tháng sau thì không — mà chính họ mới dễ tưởng nhầm kết luận được rút từ mã nguồn.

**Bịt đường lách.** `observed` trỏ vào file có đuôi mã nguồn bị từ chối thẳng, kèm chỉ dẫn dùng
`code-line` — nếu không, đổi một chữ `kind` là né được toàn bộ luật trên.

**Tầng CHAT.** `CLAUDE.md` + `AGENT.md` bắt buộc mở đầu bằng dòng `🔴 CẢNH BÁO SDK` khi một kết luận
về code tựa vào tài liệu SDK — phần chat không validator nào với tới nên đó là kỷ luật chữ.

**Đo trước khi bật:** 339 file `.md` trong `llmwiki/`, **0 báo oan**. Test: self-test PASS ·
`evidence-terminal-test.sh` 21/21 (thêm 10 ca) · `harness-doctor.py` 19/19 rails bite (R19 thêm
2 rail `callsite:bat`, `impl:im`) · drift-test 54/54 · ge-integration 12/12 · ge-acceptance 5/5 ·
ge-backcompat 14/14.

**Trần đã biết:** bộ dò lời gọi đọc MỘT DÒNG văn bản, không dựng AST — bỏ chuỗi/comment trước khi
đếm, nhận dạng khai báo của ~8 ngôn ngữ, nhưng cú pháp lạ vẫn có thể đọc nhầm cả hai chiều. Việc
"hàm này có trong repo không" tra bằng `git grep` chỉ để ĐỐI CHIẾU với khai báo của tác giả; tìm
không ra thì bỏ qua đối chiếu, cổng chính (phải khai `impl_ref` hoặc `sdk_doc`, cả hai đều có neo
kiểm được) vẫn cắn.

## Files

| File | Action |
|------|--------|
| `harness/validators/evidence_leaf.py` | modified — kind `code-line`, `call_targets`, `defines_symbol`, `_repo_defines`, `_read_anchor`, `sdk_backed_leaves`, `has_sdk_warning`, chặn `observed` trỏ file mã nguồn |
| `harness/validators/evidence_terminal.py` | modified — in cảnh báo đỏ + chặn tài liệu thiếu dấu `🔴 CẢNH BÁO SDK`; thêm 13 ca self-test |
| `llmwiki/.claude/hooks/validators/evidence_leaf.py` | modified — bản deploy tier-2, đồng bộ |
| `llmwiki/.claude/hooks/validators/evidence_terminal.py` | modified — bản deploy tier-2, đồng bộ |
| `harness/tests/evidence-terminal-test.sh` | modified — 10 fixture mới cho `code-line` + cảnh báo đỏ + đường lách `observed` |
| `harness/scripts/harness-doctor.py` | modified — R19 thêm 2 rail `callsite:bat` / `impl:im` |
| `harness/policy.yaml` | modified — statement R19 |
| `harness/poc-vendor-neutral/policy.yaml` | modified — statement R19 (bản ASCII) |
| `harness/evidence-terminal.config.yaml` | modified — ADAPT-CHECKLIST cho phần mở rộng + trần đã biết |
| `llmwiki/wiki/concepts/evidence-terminal-chain.md` | modified — mục `code-line`, mục cảnh báo đỏ, bảng 6→7 loại, ví dụ đỏ mới, giới hạn |
| `llmwiki/CLAUDE.md` | modified — tầng chat |
| `llmwiki/AGENT.md` | modified — tầng chat |
| `llmwiki/wiki/draft/cave/080926-r19-code-line-sdk-warning.md` | created |

## Notes

- Invoked via: `/caveman` skill (output report bắt buộc)
- Yêu cầu gốc: user, phiên `57250149` (nối tiếp `baebc403`), 2026-09-08
- Chưa commit — chờ `/verify-before-commit`

## Origin
- **Draft:** `wiki/draft/cave/080926-r19-code-line-sdk-warning.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
