#!/bin/bash
# parallel_post_test.sh

URL="http://172.16.16.101:8885/upload"
FILE="rfc2616.pdf"

for i in {1..10}; do
  curl -s -F "file=@$FILE" "$URL" &
done

wait
echo "All POST requests completed."
