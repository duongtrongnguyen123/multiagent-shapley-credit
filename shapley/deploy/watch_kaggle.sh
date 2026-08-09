#!/bin/bash
# Theo doi CHI cac kernel truyen vao. Chi thoat khi MOI kernel da o trang thai KET THUC
# (COMPLETE/ERROR/CANCELLED) — KHONG thoat vi mot lan goi API that bai.
cd /Users/hduong/dev/qwen-gsm8k-kaggle/shapley
export ACCOUNTS_FILE=/Users/hduong/dev/recurrent-research/accounts.txt
PY=/opt/miniconda3/bin/python; KG=/opt/miniconda3/bin/kaggle
TAGS="$@"; [ -z "$TAGS" ] && { echo "🔴 khong co kernel de theo doi"; exit 1; }
declare -A prev; declare -A done_

st_of() {  # $1=tag -> in ra trang thai, rong neu goi API loi
  local m="kernels_$1/meta.json"; [ -f "$m" ] || return
  local ref tok
  ref=$($PY -c "import json;print(json.load(open('$m'))['ref'])" 2>/dev/null) || return
  tok=$($PY -c "import json;print(json.load(open('$m'))['token'])" 2>/dev/null) || return
  KAGGLE_API_TOKEN=$tok timeout 60 $KG kernels status "$ref" 2>&1 \
    | grep -oE 'COMPLETE|ERROR|RUNNING|QUEUED|CANCEL[A-Z]*' | head -1
}
pull() { local m="kernels_$1/meta.json"
  local ref=$($PY -c "import json;print(json.load(open('$m'))['ref'])" 2>/dev/null)
  local tok=$($PY -c "import json;print(json.load(open('$m'))['token'])" 2>/dev/null)
  mkdir -p "res_$1"; KAGGLE_API_TOKEN=$tok $KG kernels output "$ref" -p "res_$1" >/dev/null 2>&1; }

for tag in $TAGS; do prev[$tag]=$(st_of $tag); done   # quet dau: im lang
while true; do
  for tag in $TAGS; do
    [ -n "${done_[$tag]}" ] && continue
    st=$(st_of $tag)
    [ -z "$st" ] && continue                          # goi API loi -> BO QUA, khong ket luan
    if [ "${prev[$tag]}" != "$st" ]; then
      case "$st" in
        COMPLETE) pull $tag; echo "✅ KAGGLE XONG: $tag — ket qua o res_$tag/"; done_[$tag]=1;;
        ERROR|CANCEL*) echo "🔴 KAGGLE LOI: $tag — $st"; done_[$tag]=1;;
      esac
      prev[$tag]=$st
    fi
  done
  # chi thoat khi TAT CA da ket thuc (dua tren done_, khong dua tren mot lan poll)
  all=1; for tag in $TAGS; do [ -z "${done_[$tag]}" ] && all=0; done
  [ "$all" -eq 1 ] && { echo "✅ tat ca $TAGS da ket thuc"; exit 0; }
  sleep 120
done
