#!/bin/bash
# parallel_get_test.sh

URL="http://172.16.16.101:8885/donalbebek.jpg"

for i in {1..20}; do
  curl -s "$URL" &
done

wait
echo "All GET requests completed."
