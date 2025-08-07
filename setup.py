from setuptools import setup, find_packages


# 读取 requirements.txt 文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith(('--', '#'))]

setup(
    name="movie_opt",
    version="0.1.0",
    include_package_data=True,  # 确保包含静态文件
    package_data={
        # 将 db 文件夹下的所有内容包含进来
        'my_package': ["db/*.db"],
    },
    packages=find_packages(),
    install_requires=read_requirements(),  # 从 requirements.txt 读取依赖
    entry_points={
        "console_scripts": [
            "movie_opt=movie_opt.main:main",
        ],
    },
)
