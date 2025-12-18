#!/bin/sh
# wait-for-it.sh: Wait for a TCP host/port to be available

TIMEOUT=15
HOST=$1
PORT=$2
shift 2
CMD="$@"

echo "⏳ Waiting for $HOST:$PORT..."

for i in $(seq $TIMEOUT); do
  nc -z "$HOST" "$PORT" > /dev/null 2>&1
  result=$?
  if [ $result -eq 0 ]; then
    echo "✅ $HOST:$PORT is available!"
    exec $CMD
  fi
  sleep 1
done

echo "❌ Timeout waiting for $HOST:$PORT"
exit 1