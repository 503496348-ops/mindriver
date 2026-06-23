from setuptools import setup, find_packages
setup(
    name="mindriver",
    version="1.0.0",
    description="Agent上下文数据库 — 文件系统范式管理记忆/资源/技能",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="智械工坊",
    url="https://github.com/503496348-ops/mindriver",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={"console_scripts": ["ov=mindriver.cli:main", "mindriver=mindriver.cli:main"]},
)
