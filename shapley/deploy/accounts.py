#!/usr/bin/env python3
"""Nguon DUY NHAT de chon tai khoan Kaggle.

LUAT (nguoi dung yeu cau, 2026-08-08):
  `zhongzhing` CHI dung khi CAN RTX 6000 Pro (no la tai khoan da join ARC-AGI-3,
  tuc la cong vao pool GPU lon). MOI viec chay T4 thong thuong PHAI tranh no.
Dung `t4_pool()` cho moi kernel T4; dung `rtx_account()` chi khi that su can 102 GB.
"""
import os, re
from pathlib import Path

RTX_ONLY = "zhongzhing"          # KHONG dung cho T4
ACCOUNTS_FILE = Path(os.environ.get("ACCOUNTS_FILE",
                     "/Users/hduong/dev/recurrent-research/accounts.txt"))

def _all():
    out = []
    for ln in ACCOUNTS_FILE.read_text().splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split()
        m = re.search(r"KGAT_[0-9a-f]+", " ".join(p[1:]))
        if m:
            out.append((p[0], m.group(0)))
    return out

def t4_pool(exclude=()):
    """Tai khoan dung duoc cho T4 — LUON loai RTX_ONLY."""
    ex = set(exclude) | {RTX_ONLY}
    return [(u, t) for u, t in _all() if u not in ex]

def rtx_account():
    """Chi goi khi that su can RTX 6000 Pro."""
    for u, t in _all():
        if u == RTX_ONLY:
            return u, t
    raise SystemExit(f"khong tim thay tai khoan {RTX_ONLY}")

if __name__ == "__main__":
    print(f"T4 dung duoc ({len(t4_pool())}):", [u for u, _ in t4_pool()])
    print(f"RTX-only: {rtx_account()[0]}  <- chi khi can 102 GB")
