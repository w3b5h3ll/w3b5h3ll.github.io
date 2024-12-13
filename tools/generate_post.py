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

    # 生成文件的路径：保存在 _posts 目录下
    posts_dir = "./../_posts"
    os.makedirs(posts_dir, exist_ok=True)

    # 保存文件到 _posts 目录
    post_path = os.path.join(posts_dir, filename)
    with open(post_path, "w") as f:
        f.write(frontmatter)

    # 创建同名文件夹：保存图片的文件夹在 ../assets/images 目录下
    folder_name = f"{date_str}-{title_slug}"
    images_dir = "./../assets/images"
    os.makedirs(os.path.join(images_dir, folder_name), exist_ok=True)

    print(f"Markdown 文件已生成: {post_path}")
    print(f"同名文件夹已生成: {os.path.join(images_dir, folder_name)}")
    return post_path

# 示例使用
title = input("请输入文章标题: ")
generate_jekyll_post(title)

