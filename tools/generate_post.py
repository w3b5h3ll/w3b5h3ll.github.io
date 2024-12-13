import os
from datetime import datetime

def generate_jekyll_post(title):
    # 获取当前日期和时间
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 将标题转换为文件名格式
    title_slug = "-".join(title.lower().split())
    filename = f"{date_str}-{title_slug}.md"

    # 定义 frontmatter 内容
    frontmatter = f"""---
title: "{title}"
date: {datetime_str}
tags:
---

"""

    # 创建同名文件夹
    folder_name = f"{date_str}-{title_slug}"
    os.makedirs(folder_name, exist_ok=True)

    # 保存文件到主目录中
    with open(filename, "w") as f:
        f.write(frontmatter)

    print(f"Markdown 文件已生成: {filename}")
    print(f"同名文件夹已生成: {folder_name}")
    return filename

# 示例使用
title = input("请输入文章标题: ")
generate_jekyll_post(title)

