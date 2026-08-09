#!/bin/bash
# Phat SU KIEN (moi dong = mot thong bao) khi: job XONG, job LOI, GPU roi ma con hang doi,
# hoac mat ket noi. Chi phat khi CO THAY DOI -> khong spam.
H="root@180.189.55.43"; P=41756
SSH="ssh -p $P -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=10"
seen_end=""; seen_err=""; idle_reported=0; fail_streak=0

while true; do
  OUT=$($SSH $H '
    grep -E "^[0-9:]+ END" /root/supervisor.log 2>/dev/null | tail -30 | sed "s/^/END|/"
    for f in /root/log_*.txt; do
      [ -f "$f" ] || continue
      if grep -qE "Traceback|OutOfMemoryError|ModuleNotFoundError|AssertionError|CUDA error" "$f" 2>/dev/null; then
        echo "ERR|$(basename $f .txt)|$(grep -hoE "Traceback|OutOfMemoryError|ModuleNotFoundError|AssertionError|CUDA error" "$f" | tail -1)"
      fi
    done
    U=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
    W=$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits | head -1)
    Q=$(grep -vcE "^\s*$" /root/queue.txt 2>/dev/null || echo 0)
    N=$(pgrep -cf "_local[.]py" 2>/dev/null || echo 0)
    echo "STATE|$U|$W|$Q|$N"
  ' 2>/dev/null)

  if [ -z "$OUT" ]; then
    fail_streak=$((fail_streak+1))
    [ "$fail_streak" -eq 2 ] && echo "🔴 REMOTE KHONG KET NOI DUOC (2 lan lien tiep) — may co the da tat"
    sleep 60; continue
  fi
  fail_streak=0

  # 1) job vua XONG
  while IFS= read -r line; do
    case "$line" in END\|*)
      e="${line#END|}"
      case "$seen_end" in *"$e"*) ;; *) echo "✅ XONG: $e"; seen_end="$seen_end;$e";; esac;;
    esac
  done <<< "$OUT"

  # 2) job co LOI
  while IFS= read -r line; do
    case "$line" in ERR\|*)
      e="${line#ERR|}"
      case "$seen_err" in *"$e"*) ;; *) echo "🔴 LOI: $e"; seen_err="$seen_err;$e";; esac;;
    esac
  done <<< "$OUT"

  # 3) GPU roi ma van con hang doi -> BAO NGAY
  S=$(echo "$OUT" | grep "^STATE|" | tail -1)
  U=$(echo "$S"|cut -d'|' -f2); W=$(echo "$S"|cut -d'|' -f3)
  Q=$(echo "$S"|cut -d'|' -f4); N=$(echo "$S"|cut -d'|' -f5)
  if [ "${U:-0}" -lt 5 ] && [ "${N:-0}" -eq 0 ]; then
    if [ "$idle_reported" -eq 0 ]; then
      if [ "${Q:-0}" -gt 0 ]; then echo "🟠 GPU ROI (${U}% ${W}W) NHUNG CON $Q JOB TRONG HANG DOI — supervisor co van de"
      else echo "🟡 GPU ROI (${U}% ${W}W) va HANG DOI RONG — can nap viec moi"; fi
      idle_reported=1
    fi
  else idle_reported=0; fi
  sleep 60
done
