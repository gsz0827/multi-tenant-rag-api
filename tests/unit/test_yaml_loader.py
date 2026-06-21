import pytest

from tests.helpers.yaml_loader import load_yaml


@pytest.mark.unit
def test_load_auth_cases_yaml():
    """
    测试能否正确读取 auth_cases.yaml
    """

    # 读取认证相关测试数据
    data = load_yaml("auth_cases.yaml")

    # 校验 yaml 中存在注册成功用例
    assert "register_success" in data

    # 校验注册用例中的邮箱字段
    assert data["register_success"]["email"] == "test_user@example.com"

    # 校验期望状态码
    assert data["register_success"]["expected_status"] == 200


@pytest.mark.unit
def test_load_knowledge_base_cases_yaml():
    """
    测试能否正确读取 knowledge_base_cases.yaml
    """

    # 读取知识库相关测试数据
    data = load_yaml("knowledge_base_cases.yaml")

    # 校验创建知识库成功用例存在
    assert "create_success" in data

    # 校验知识库名称字段
    assert data["create_success"]["name"] == "自动化测试知识库"


@pytest.mark.unit
def test_load_document_cases_yaml():
    """
    测试能否正确读取 document_cases.yaml
    """

    # 读取文档上传相关测试数据
    data = load_yaml("document_cases.yaml")

    # 校验 txt 上传成功用例存在
    assert "txt_upload_success" in data

    # 校验文件类型
    assert data["txt_upload_success"]["content_type"] == "text/plain"


@pytest.mark.unit
def test_load_rag_cases_yaml():
    """
    测试能否正确读取 rag_cases.yaml
    """

    # 读取 RAG 问答相关测试数据
    data = load_yaml("rag_cases.yaml")

    # 校验正常问答用例存在
    assert "ask_success" in data

    # 校验问题字段不为空
    assert data["ask_success"]["question"] != ""