#!/usr/bin/env bash
# Runs the seven tests in level-2/scope.md exactly as written. Each prints PASS or FAIL.
# Usage, from level-2/rent-roll-count:  bash run_tests.sh
cd "$(dirname "$0")"
F=fixtures; S=rent_roll_count.py; pass=0; fail=0
result() { if [ "$1" = 0 ]; then echo "PASS  $2"; pass=$((pass+1)); else echo "FAIL  $2"; fail=$((fail+1)); fi; }

# T1: Cedar Ridge output matches the expected file exactly, exit 0
out=$(python "$S" $F/cedar-ridge.csv 2>&1); rc=$?
[ $rc = 0 ] && [ "$out" = "$(cat $F/expected-cedar-ridge.txt)" ]; result $? "T1 Cedar Ridge matches expected output"
[ "$out" = "$(cat $F/expected-cedar-ridge.txt)" ] || diff <(echo "$out") $F/expected-cedar-ridge.txt | sed 's/^/      /'

# T2: shuffled rows give identical output
out2=$(python "$S" $F/cedar-ridge-shuffled.csv 2>&1)
[ "$out2" = "$(cat $F/expected-cedar-ridge.txt)" ]; result $? "T2 shuffled rows give identical output"

# T3: rents written as "$1,450" give identical output
out3=$(python "$S" $F/dollar-format.csv 2>&1)
[ "$out3" = "$(cat $F/expected-cedar-ridge.txt)" ]; result $? "T3 \$1,450-style rents give identical output"
[ "$out3" = "$(cat $F/expected-cedar-ridge.txt)" ] || echo "$out3" | head -3 | sed 's/^/      /'

# T4-T6: bad input -> exit 1, stderr one line starting "Error:" naming the unit, no traceback, nothing on stdout
bad() { # file unit label
  so=$(python "$S" "$F/$1" 2>/tmp/rrc_err); rc=$?; se=$(cat /tmp/rrc_err)
  [ $rc = 1 ] && [ -z "$so" ] && [ "$(echo "$se" | wc -l)" = 1 ] && [[ "$se" == Error:* ]] && [[ "$se" == *"$2"* ]] && [[ "$se" != *Traceback* ]]
  result $? "$3"
  echo "      exit=$rc stderr: $(echo "$se" | head -2 | tr '\n' ' ')"
}
bad duplicate-unit.csv 105 "T4 duplicate unit 105 is refused"
bad blank-rent.csv 107 "T5 blank rent on unit 107 is refused"
bad odd-status.csv 104 "T6 status 'Notice' on unit 104 is refused"

# T7: missing file -> exit 1, one-line Error:, no traceback
so=$(python "$S" $F/no-such-file.csv 2>/tmp/rrc_err); rc=$?; se=$(cat /tmp/rrc_err)
[ $rc = 1 ] && [ "$(echo "$se" | wc -l)" = 1 ] && [[ "$se" == Error:* ]] && [[ "$se" != *Traceback* ]]; result $? "T7 missing file gives a one-line error"
echo "      exit=$rc stderr: $(echo "$se" | head -2 | tr '\n' ' ')"

echo; echo "$pass passed, $fail failed"
