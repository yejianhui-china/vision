#!/usr/bin/env bash
# 一键停止前后端服务

echo "Stopping services..."

# 停止前端 (Node)
for pid in $(ps -W | grep node | awk '{print $1}'); do
    taskkill //PID "$pid" //F 2>/dev/null || true
done

# 停止后端 (Python)
for pid in $(ps -W | grep python | awk '{print $1}'); do
    taskkill //PID "$pid" //F 2>/dev/null || true
done

echo "Done!"
