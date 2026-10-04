---
type: unknown-ledger
title: "unknown — 031026-harness-claude-orca-integration"
status: open
source_task: T-261003-01
source_spec: wiki/sources/draft/031026-harness-claude-orca-integration.md
timestamp: 2026-10-03
---

# Unknown ledger — 031026-harness-claude-orca-integration

> **Nợ unknown** — model đã *fill-first* (điền default để không chặn việc), *find-out-later* (chờ thông tin thật để trả nợ). KHÔNG chặn cổng; hiện ra ở `/lint` để không chìm. Đóng khoảng hở giữa `(default)` và `[CẦN LÀM RÕ]`. Xem `[[150726-unknown-ledger]]`.
>
> Thêm/đóng mục bằng `python3 harness/scripts/unknown-ledger.py` — đừng sửa số U-NN bằng tay.

## U-02 — Orca có một sổ task dùng chung; lọc theo project có đủ tránh claim nhầm, hay Orca có không gian tên gốc?
- **Trace:** FR-006 · SPEC `llmwiki/wiki/sources/draft/031026-harness-claude-orca-integration.md` · task `T-261003-01`
- **Đã fill (default):** Lọc theo trường project ở phía harness
- **Cần verify:** Chạy fixture Task 7 với hai repo cùng lúc
- **Rủi ro nếu default sai:** medium
- **Status:** open
- **Resolved:** _(chưa)_

## Origin
- Sinh bởi `/propose` khi user chọn "fill-first, find-out-later" cho một unknown của SPEC nguồn.
- Trả nợ: `unknown-ledger.py --resolve <file> <U-id> --value … --fixed … --date …`.
- **Commit:** _(verify-before-commit điền)_
