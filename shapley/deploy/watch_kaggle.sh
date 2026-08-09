#!/bin/bash
# Phat su kien khi kernel Kaggle CHUYEN TRANG THAI (xong / loi). Chi bao khi CO THAY DOI.
cd /Users/hduong/dev/qwen-gsm8k-kaggle/shapley
export ACCOUNTS_FILE=/Users/hduong/dev/recurrent-research/accounts.txt
PY=/opt/miniconda3/bin/python; KG=/opt/miniconda3/bin/kaggle
declare -A prev
while true; do
  for m in kernels_*/meta.json; do
    d=$(dirname "$m"); tag=${d#kernels_}
    # chi theo doi kernel chua co ket qua
    [ -f "res_$tag/summary.json" ] && continue
    ref=$($PY -c "import json;print(json.load(open('$m'))['ref'])" 2>/dev/null) || continue
    tok=$($PY -c "import json;print(json.load(open('$m'))['token'])" 2>/dev/null) || continue
    st=$(KAGGLE_API_TOKEN=$tok $KG kernels status "$ref" 2>&1 | grep -oE 'COMPLETE|ERROR|RUNNING|QUEUED|CANCEL[A-Z]*')
    [ -z "$st" ] && continue
    if [ "${prev[$tag]}" != "$st" ]; then
      case "$st" in
        COMPLETE) mkdir -p "res_$tag"
                  KAGGLE_API_TOKEN=$tok $KG kernels output "$ref" -p "res_$tag" >/dev/null 2>&1
                  echo "✅ KAGGLE XONG: $tag ($ref) — da keo ket qua ve res_$tag/";;
        ERROR|CANCEL*) echo "🔴 KAGGLE LOI: $tag ($ref) — trang thai $st";;
      esac
      prev[$tag]=$st
    fi
  done
  sleep 120
done
