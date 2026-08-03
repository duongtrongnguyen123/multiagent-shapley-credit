#!/usr/bin/env python3
"""Lớp NLP #3 (HEADLINE) — LEARNED CREDIT CRITIC. Train một model NLP đọc TOÀN BỘ
transcript (plan/solver/verifier/aggregator) -> dự đoán đáp án cuối ĐÚNG/SAI. Sau đó
MASK từng message rồi đo P(đúng) tụt/tăng bao nhiêu = đóng góp của message đó — Shapley
cấp *message* bằng mô hình NLP, thay vì bật/tắt role. LOCAL/CPU (TF-IDF + LogReg).

Cần đủ dữ liệu: >=~150 trace (sinh trên Kaggle bằng trace_kernel). Với ít trace thì AUC
không tin được — script vẫn chạy nhưng báo cảnh báo."""
import json, numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score

BASE = Path(__file__).resolve().parents[1]
T = json.loads((BASE / "results_trace/traces.json").read_text())
ROLES = [("P", "plan"), ("S", "sol"), ("V", "ver"), ("A", "agg")]

def transcript(t, drop=None):
    parts = []
    for tag, key in ROLES:
        if tag == drop:
            continue
        parts.append(f"[{tag}] {t.get(key, '')}")
    return "\n".join(parts)

y = np.array([1 if t.get("a_ok", t.get("v_ok")) else 0 for t in T])   # đúng/sai cuối
X = [transcript(t) for t in T]
print(f"{len(T)} trace | tỉ lệ đúng = {y.mean():.2f}")
if len(T) < 120 or y.mean() in (0.0, 1.0):
    print("⚠️  quá ít trace / nhãn lệch -> critic chưa tin được. Hãy scale trace generation.")

def fit():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000),
                         LogisticRegression(max_iter=1000, class_weight="balanced"))
# AUC bằng cross-val (transcript đầy đủ dự đoán đúng/sai được không?)
try:
    p = cross_val_predict(fit(), X, y, cv=5, method="predict_proba")[:, 1]
    print(f"Critic AUC (transcript -> đúng/sai) = {roc_auc_score(y, p):.3f}")
except Exception as e:
    print("cross-val lỗi (ít data):", e)

# Credit từng role = mức tụt P(đúng) khi MASK role đó
clf = fit().fit(X, y)
base_p = clf.predict_proba(X)[:, 1]
print(f"\n{'role':11s} {'ΔP(đúng) khi bỏ':>18s}")
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}
for tag, _ in ROLES:
    masked = [transcript(t, drop=tag) for t in T]
    dp = float(np.mean(base_p - clf.predict_proba(masked)[:, 1]))   # >0 = role đó GIÚP dự đoán đúng
    print(f"{NAMES[tag]:11s} {dp:>+18.4f}")
print("\n(ΔP>0: bỏ message role đó làm critic bớt tự tin -> role mang thông tin có ích;")
print(" ΔP<0: message role đó gây nhiễu. Đây là credit dựa trên NỘI DUNG, học được.)")
