#!/bin/bash
# Chi theo doi cac kernel TRUYEN VAO (khong quet toan bo lich su).
# Dung: watch_kaggle.sh tag1 tag2 ...
cd /Users/hduong/dev/qwen-gsm8k-kaggle/shapley
export ACCOUNTS_FILE=/Users/hduong/dev/recurrent-research/accounts.txt
PY=/opt/miniconda3/bin/python; KG=/opt/miniconda3/bin/kaggle
TAGS="$@"
[ -z "$TAGS" ] && { echo "🔴 khong co kernel nao de theo doi"; exit 1; }
declare -A prev
# lan quet DAU: chi ghi nhan trang thai, KHONG bao (tranh phat lai lich su)
for tag in $TAGS; do
  m="kernels_$tag/meta.json"; [ -f "$m" ] || continue
  ref=$($PY -c "import json;print(json.load(open('$m'))['ref'])" 2>/dev/null)
  tok=$($PY -c "import json;print(json.load(open('$m'))['token'])" 2>/dev/null)
  prev[$tag]=$(KAGGLE_API_TOKEN=$tok $KG kernels status "$ref" 2>&1 | grep -oE 'COMPLETE|ERROR|RUNNING|QUEUED|CANCEL[A-Z]*')
done
while true; do
  live=0
  for tag in $TAGS; do
    m="kernels_$tag/meta.json"; [ -f "$m" ] || continue
    [ "${prev[$tag]}" = "COMPLETE" ] && continue
    case "${prev[$tag]}" in ERROR|CANCEL*) continue;; esac
    ref=$($PY -c "import json;print(json.load(open('$m'))['ref'])" 2>/dev/null)
    tok=$($PY -c "import json;print(json.load(open('$m'))['token'])" 2>/dev/null)
    st=$(KAGGLE_API_TOKEN=$tok $KG kernels status "$ref" 2>&1 | grep -oE 'COMPLETE|ERROR|RUNNING|QUEUED|CANCEL[A-Z]*')
    [ -z "$st" ] && continue
    live=1
    if [ "${prev[$tag]}" != "$st" ]; then
      case "$st" in
        COMPLETE) mkdir -p "res_$tag"
                  KAGGLE_API_TOKEN=$tok $KG kernels output "$ref" -p "res_$tag" >/dev/null 2>&1
                  echo "✅ KAGGLE XONG: $tag — ket qua o res_$tag/";;
        ERROR|CANCEL*) echo "🔴 KAGGLE LOI: $tag ($ref) — $st";;
      esac
      prev[$tag]=$st
    fi
  done
  [ "$live" -eq 0 ] && { echo "✅ tat ca kernel theo doi da ket thuc"; exit 0; }
  sleep 120
done
