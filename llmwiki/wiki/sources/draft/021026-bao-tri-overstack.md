---
type: draft
title: "021026-bao-tri-overstack"
status: proposed
tags: [docs-site-macos, output-report, uninstall, harness, wikieval]
timestamp: 2026-10-02
---

# 021026-bao-tri-overstack
**Type:** draft
**Status:** proposed
**Tags:** docs-site-macos, output-report
**Proposed:** 2026-10-02

## What
Tổng hợp năm việc bảo trì overstack từ 27/09 đến 02/10/2026 thành một trang tài liệu HTML: lệnh gỡ overstack khỏi dự án, cập nhật harness global, đồng bộ fork với upstream, bỏ phần việc dở của phiên dsh, và khoá hồi quy cho các bản sửa.

## Output
Trang `llmwiki/html/021026-bao-tri-overstack.html` gồm bảy mục. Trang qua cổng tĩnh (0 cảnh báo), cổng chạy thật (1/1), R20 và R22, và Playwright audit (sidebar đóng mở được, nút đổi theme nằm trong nav, không có request ra ngoài, có mind map). Thư mục `llmwiki/html/` không được commit nên trang chỉ nằm trên máy.

Các thay đổi mà trang mô tả đã nằm ở nơi khác:
- Lệnh gỡ (`bootstrap.sh … uninstall`, `uninstall.sh` viết lại cho layout v4) và test `uninstall-roundtrip` ở PR #199, đã merge vào fork `c970b388`. Bản cũ đỏ 11/17 check, bản mới đạt 17/17.
- Test hồi quy `fdk-gate-git-env` và golden `fdk-gate-git-env` ở PR #173. Bản trước khi sửa làm rò `GIT_DIR` và commit lén vào repo ngoài (1 → 2 commit).
- Golden `uninstall-turns-off-harness` ở PR #199.
- Harness global trên máy lên 1.3.125.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/021026-bao-tri-overstack.html` | created (local, không commit) |
| `llmwiki/wiki/sources/draft/021026-bao-tri-overstack.md` | created |
| `llmwiki/wiki/index.md` | modified |

## Notes
- Invoked via: `/docs-site-macos` skill.
- Không thêm dòng vào `llmwiki/wiki/log.md` bằng tay: file này do máy render lại từ sổ sự kiện (R4), sửa tay sẽ bị ghi đè ở lượt sau.
- Việc còn mở: chờ upstream review #173, #174, #175, #199; `install.ps1` chưa có cờ gỡ; chưa có lệnh gỡ engine global; `.codex/` và `AGENTS.md` chưa rõ nguồn.

## Origin
- **Draft:** `wiki/sources/draft/021026-bao-tri-overstack.md`
- **Phiên:** `2601b4e7-0818-49d3-8c11-534771fc4618`, yêu cầu của user ngày 02/10/2026 ("thêm command để gỡ harness khỏi dự án, làm việc 1 và 2").
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
