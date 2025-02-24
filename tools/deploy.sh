#!/bin/bash

# 移动到上级目录
cd ../ || { echo "cd ../ failed"; exit 1; }

# 执行 Prettier 格式化
npx prettier --write "./_posts/*.md" || { echo "Prettier format failed"; exit 1; }

# 添加所有更改
git add . || { echo "git add failed"; exit 1; }

# 获取当前日期和时间
commit_message=$(date +"%Y-%m-%d %H:%M:%S")

# 提交更改
git commit -m "$commit_message" || { echo "git commit failed"; exit 1; }

# 推送更改
git push || { echo "git push failed"; exit 1; }

echo "所有命令执行成功"

