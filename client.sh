#!/bin/bash

CONTAINER_LIST=("docker-api_server-1-1" "docker-api_server-2-1")
LOG_LINES=1

INTERVAL_SECONDS=5

while true; do
  for CONTAINER_NAME in "${CONTAINER_LIST[@]}"; do
    LOG_OUTPUT=$(docker logs $CONTAINER_NAME -n $LOG_LINES)

    JSON_DATA="{\"server_name\":\"$SERVER_NAME\",\"container_name\":\"$CONTAINER_NAME\",\"log_content\":\"$LOG_OUTPUT\"}"

    curl -X POST \
      -H "Content-Type: application/json" \
      -d "$JSON_DATA" \
      $REPORT_TARGET
  done

  # 等待指定时间
  sleep $INTERVAL_SECONDS
done
