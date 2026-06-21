import os

import pytest
from faker import Faker


# ==============================
# 设置测试环境变量
# 必须尽量放在导入 app 之前
# ==============================

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("API_PREFIX", "/api")

# 测试环境使用 fake embedding，避免调用真实外部 embedding 服务
os.environ.setdefault("EMBEDDING_PROVIDER", "fake")


# ==============================
# Faker 用来生成随机测试数据
# 避免邮箱、用户名重复
# ==============================

fake = Faker()


@pytest.fixture()
def client():
    """
    FastAPI 测试客户端 fixture

    作用：
    1. 模拟 HTTP 请求
    2. 不需要手动启动 uvicorn
    3. 用于接口自动化测试
    """

    # 延迟导入 app，避免环境变量还没设置好就加载配置
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def api_client(client):
    """
    API Client fixture

    作用：
    1. 封装接口请求
    2. 管理 token
    3. 简化测试用例代码
    """

    from tests.helpers.api_client import ApiClient

    return ApiClient(client)


@pytest.fixture()
def user_payload():
    """
    生成随机注册用户数据

    每次测试都会生成不同邮箱，
    避免重复注册导致测试失败。
    """

    return {
        "email": fake.email(),
        "username": fake.user_name(),
        "full_name": fake.name(),
        "password": "TestPassword123"
    }


@pytest.fixture()
def registered_user(api_client, user_payload):
    """
    注册一个测试用户

    返回：
        email: 用户邮箱
        username: 用户名
        password: 原始密码
        user_info: 注册接口返回的用户信息
    """

    response = api_client.register(user_payload)

    assert response.status_code == 200, response.text

    return {
        "email": user_payload["email"],
        "username": user_payload["username"],
        "password": user_payload["password"],
        "user_info": response.json()
    }


@pytest.fixture()
def logged_in_api_client(api_client, registered_user):
    """
    返回一个已登录的 ApiClient

    流程：
    1. 先通过 registered_user fixture 注册用户
    2. 再调用登录接口获取 token
    3. 把 token 保存进 api_client
    4. 后续请求自动携带 Authorization 请求头
    """

    response = api_client.login(
        username=registered_user["email"],
        password=registered_user["password"]
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    api_client.set_token(token)

    return api_client


@pytest.fixture()
def organization_id(logged_in_api_client):
    """
    获取当前登录用户所属的组织 ID

    背景：
    用户注册成功后，系统通常会自动创建一个默认组织。
    创建知识库时需要传 organization_id。
    """

    # 查询当前用户所属组织
    response = logged_in_api_client.list_organizations()

    # 校验接口调用成功
    assert response.status_code == 200, response.text

    organizations = response.json()

    # 校验当前用户至少属于一个组织
    assert len(organizations) > 0, "当前用户没有所属组织，无法创建知识库"

    # 返回第一个组织 ID
    return organizations[0]["id"]


@pytest.fixture()
def created_knowledge_base(logged_in_api_client, organization_id):
    """
    创建一个测试知识库

    作用：
    后续测试查询详情、删除、文档上传时都可以复用这个知识库。
    """

    payload = {
        "organization_id": organization_id,
        "name": "fixture 创建的测试知识库",
        "description": "这是 conftest.py 中 fixture 自动创建的知识库"
    }

    # 调用创建知识库接口
    response = logged_in_api_client.create_knowledge_base(payload)

    # 校验创建成功
    assert response.status_code == 200, response.text

    # 返回知识库信息
    return response.json()