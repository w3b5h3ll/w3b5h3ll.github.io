#!/bin/bash

# 移动到上级目录
cd ../ || {
    echo "cd ../ failed"
    exit 1
}

# 执行 Prettier 格式化
npx prettier --write "./_posts/*.md" || { echo "Prettier format failed"; exit 1; }

bundle exec jekyll s || {
    echo "run local failed"
    exit 1
}
