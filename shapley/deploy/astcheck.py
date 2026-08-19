#!/usr/bin/env python3
"""Kiem cu phap TOAN BO pipeline/*.py sau moi lan sua (quy tac cung cua du an).

Vi sao co file nay: bo kiem tam thoi cua toi thay 16 kernel "hong cu phap" — that ra chung
dung placeholder (`@@SHARD@@`, `@@NSHARD@@`, ...) ma bo kiem khong biet cach thay. Mot bo kiem
bao dong gia 16 lan la bo kiem se bi phot lo. Bo nay thay MOI `@@TEN@@` bang mot literal hop le.

Dung:  python deploy/astcheck.py            # tat ca
       python deploy/astcheck.py a.py b.py  # rieng le
Ma thoat != 0 neu co file hong  ->  dung duoc trong tien-kiem truoc khi phong.
"""
import ast, glob, re, sys

PH = re.compile(r"@@([A-Z_][A-Z0-9_]*)@@")
# placeholder nao phai la SO thi thay bang so, con lai thay bang chuoi
NUMERIC = {"LO", "HI", "SIZE", "SHARD", "NSHARD", "K", "N", "SEED", "FOLD", "KMAX", "TIDLO", "TIDHI"}

def defuse(src: str) -> str:
    """Thay moi @@TEN@@ bang literal hop le, giu nguyen do dai dong cang nhieu cang tot."""
    def sub(m):
        name = m.group(1)
        return "1" if name in NUMERIC else "x"
    return PH.sub(sub, src)

def check(paths):
    bad = []
    for p in paths:
        try:
            src = open(p, encoding="utf-8").read()
        except OSError as e:
            bad.append((p, f"khong doc duoc: {e}")); continue
        left = set(PH.findall(src))
        try:
            ast.parse(defuse(src))
        except SyntaxError as e:
            bad.append((p, f"dong {e.lineno}: {e.msg}"))
            continue
        # canh bao (khong phai loi): placeholder la, launcher se chan luc phong
        unknown = left - {"RUN", "LO", "HI", "SIZE", "DEAR"}
        if unknown:
            print(f"  ghi chu  {p}: placeholder ngoai bo launcher biet = {sorted(unknown)}")
    return bad

if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob("pipeline/*.py"))
    bad = check(paths)
    print(f"\nda kiem {len(paths)} file | HONG: {len(bad)}")
    for p, r in bad:
        print(f"  HONG  {p}: {r}")
    sys.exit(1 if bad else 0)
