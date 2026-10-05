---
type: draft
title: "Gap analysis + SPEC port ngược cơ chế PLAN-2→4 của DSH về overstack"
tags: [caveman, output-report, propose, backport, dsh]
timestamp: 2026-09-30
---

# 300926-dsh-backport-propose
**Type:** draft
**Status:** proposed
**Tags:** propose, output-report
**Proposed:** 2026-09-30

## What
Đối chiếu mười sáu package experimental của DeepSeek Harness (nhánh `dragonwar000/newfeature`) với overstack, rồi viết SPEC 14 task port các luật tất định vào hook của overstack; dừng ở cổng duyệt, chưa sửa mã.

## Output
- Bảng đối chiếu 19 cơ chế: 15 dẫn tới một task, 4 không port (fresh evaluator, graph-runner riêng, protectUnseen và summary convergence, history_read; cycleGuard ánh xạ sang `loop-runner.py`).
- SPEC có 24 FR, 7 SC, 14 task, mọi guard mặc định `shadow`.
- Task id `T-260930-01`.

## Files
| File | Action |
|------|--------|
| `llmwiki/wiki/sources/draft/300926-dsh-loop-graph-knowledge-backport-harness.md` | created |
| `llmwiki/html/300926-dsh-loop-graph-knowledge-backport-seq.html` | created |
| `llmwiki/wiki/index.md` | modified |
| `llmwiki/wiki/log.md` | modified |
| `harness/metrics/tasks.json` | modified (task mới qua `code-logger.py --task new`) |

## Notes
- Invoked via: `/propose` skill
- Thay đổi R19 `code-line` đang dở trong working tree không bị đụng.

## Origin
- **Draft:** `wiki/draft/cave/300926-dsh-backport-propose.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
