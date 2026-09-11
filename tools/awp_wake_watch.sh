#!/bin/sh
# AWP wake watcher for hosted agents (Cooperation Contracts section 12, W1 git-signal).
#
# Run by a background hook that wakes the agent when this script exits with
# code 2 (for Claude: a Stop hook with "asyncRewake": true).  It waits for the
# agent's content-free wake-signal ref on a Git remote to change, then exits 2
# with a one-line doorbell naming the command to run.  It never reads message
# content; the agent reads the ledger itself after it wakes.
#
# usage: awp_wake_watch.sh <remote-url> <signal-ref> <actor> [state-dir] [interval-seconds]
set -u
url=$1; ref=$2; actor=$3
state_dir=${4:-${TMPDIR:-/tmp}/awp-wake}
interval=${5:-15}
mkdir -p "$state_dir" || exit 0
key=$(printf '%s %s' "$url" "$ref" | cksum | cut -d' ' -f1)
seen="$state_dir/$key.seen"
lock="$state_dir/$key.lock"

# One watcher per signal: a second hook invocation leaves the first in place.
if ! mkdir "$lock" 2>/dev/null; then
  if [ -f "$lock/pid" ] && kill -0 "$(cat "$lock/pid")" 2>/dev/null; then
    exit 0
  fi
  rm -rf "$lock"; mkdir "$lock" 2>/dev/null || exit 0
fi
echo $$ > "$lock/pid"
trap 'rm -rf "$lock"' EXIT INT TERM

current() {
  GIT_TERMINAL_PROMPT=0 git ls-remote "$url" "$ref" 2>/dev/null | cut -f1
}

last=$(cat "$seen" 2>/dev/null || true)
if [ -z "$last" ]; then
  last=$(current)
  [ -n "$last" ] || last=none
  echo "$last" > "$seen"
fi

while :; do
  now=$(current)
  if [ -n "$now" ] && [ "$now" != "$last" ]; then
    echo "$now" > "$seen"
    echo "[AWP doorbell] New wake signal for $actor. As your next action, run exactly \`python -m tools.awp_wake pending --actor $actor --ack\` from the AWP project root; it records receipt for what is waiting and grants no authority." >&2
    exit 2
  fi
  sleep "$interval"
done
