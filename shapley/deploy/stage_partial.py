#!/usr/bin/env python3
"""Dua mot `partial_*.json` len Kaggle thanh DATASET de lan chay sau NAP LAI thay vi sinh lai.

Vi sao (#196 phat hien, #199 tinh lai lan hai):
  Greedy TAT DINH — hai lan chay cung (may + do chinh xac + bo bai + model) cho ket qua
  **giong het tung bai** (kiem: 499/499, hai tai khoan, hai ngay). Nen sinh lai mot nhanh da co
  la **lang phi thuan tuy**. H100e phai tao lai ~4.8 gio GPU du lieu da nam san trong
  `partial_H100d.json`.

AN TOAN — kernel chi duoc nap lai khi KHOP TUONG MINH (xem `resume_raw` trong kernel):
  cung `n`, cung danh sach `task_id`, cung ten nhanh. Khong khop thi SINH LAI, khong doan.
  Va `res_*.json` phai ghi ro nhanh nao NAP LAI, nhanh nao SINH MOI.

Dung:
    python deploy/stage_partial.py results_H100d/partial_H100d.json tuetrandoanminh
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACC = Path(os.environ.get("ACCOUNTS", "/Users/hduong/dev/recurrent-research/accounts.txt"))

def token_for(user):
    for line in ACC.read_text().splitlines():
        p = line.split()
        if len(p) >= 2 and p[0] == user: return p[1]
    sys.exit(f"khong thay tai khoan {user} trong {ACC}")

def main():
    if len(sys.argv) < 3:
        sys.exit("dung: python deploy/stage_partial.py <partial_X.json> <kaggle_user>")
    src, user = Path(sys.argv[1]), sys.argv[2]
    if not src.is_file(): sys.exit(f"khong thay {src}")

    d = json.load(open(src))
    arms = sorted(d.get("raw", {}).keys())
    n = d.get("n")
    if not arms or not n: sys.exit("partial khong co `raw` hoac `n` — khong dung duoc")
    if "task_id" not in d and "gold" not in d:
        sys.exit("partial thieu CA `task_id` LAN `gold` — khong the kiem khop, TU CHOI dua len")
    print(f"  {src.name}: n={n}, {len(arms)} nhanh: {arms}")

    slug = f"resume-{src.stem.replace('_','-').lower()}"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / src.name).write_text(json.dumps(d))
        (td / "dataset-metadata.json").write_text(json.dumps({
            "title": slug, "id": f"{user}/{slug}", "licenses": [{"name": "CC0-1.0"}]}, indent=1))
        env = dict(os.environ, KAGGLE_API_TOKEN=token_for(user))
        r = subprocess.run(["kaggle", "datasets", "create", "-p", str(td), "-r", "zip"],
                           env=env, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        if "already exists" in out:
            r = subprocess.run(["kaggle", "datasets", "version", "-p", str(td),
                                "-m", "cap nhat", "-r", "zip"], env=env, capture_output=True, text=True)
            out = (r.stdout or "") + (r.stderr or "")
        print(out.strip()[-400:])
    print(f"\n  -> them vao DATASETS khi phong: {user}/{slug}")
    print("     va kernel phai goi resume_raw() — no TU KIEM khop truoc khi nap.")

if __name__ == "__main__":
    main()
