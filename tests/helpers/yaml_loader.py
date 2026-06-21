from pathlib import Path
import yaml


# ==============================
# 获取 tests 目录路径
# 当前文件路径是 tests/helpers/yaml_loader.py
# parents[1] 就是 tests 目录
# ==============================
TESTS_DIR = Path(__file__).resolve().parents[1]


# ==============================
# 测试数据目录：tests/data
# ==============================
DATA_DIR = TESTS_DIR / "data"


def load_yaml(file_name: str):
    """
    读取 tests/data 目录下的 yaml 测试数据文件

    参数：
        file_name: yaml 文件名，例如 auth_cases.yaml

    返回：
        dict/list: yaml 文件解析后的 Python 数据
    """

    # 拼接完整文件路径
    file_path = DATA_DIR / file_name

    # 如果文件不存在，直接抛出清晰的错误，方便定位问题
    if not file_path.exists():
        raise FileNotFoundError(f"测试数据文件不存在: {file_path}")

    # 使用 safe_load 读取 yaml，避免 yaml.load 的安全风险
    with file_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)