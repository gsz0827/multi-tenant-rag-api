import pytest
import allure

from tests.helpers.yaml_loader import load_yaml
from tests.helpers.assertions import (
    assert_status_code,
    assert_json_has_keys,
    assert_value_equal,
    attach_response,
)


@allure.epic("多租户 RAG 系统")
@allure.feature("知识库管理模块")
class TestKnowledgeBaseApi:
    """
    知识库接口测试

    覆盖范围：
    1. 查询当前用户所属组织
    2. 创建知识库
    3. 查询知识库列表
    4. 查询知识库详情
    5. 未登录创建知识库失败
    """

    @allure.story("组织查询")
    @allure.title("登录后查询当前用户所属组织列表成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_list_organizations_success(self, logged_in_api_client):
        """
        测试登录后可以查询当前用户所属组织列表
        """

        with allure.step("1. 调用组织列表接口"):
            response = logged_in_api_client.list_organizations()
            attach_response(response, "组织列表接口响应")

        with allure.step("2. 校验接口状态码为 200"):
            assert_status_code(response, 200)

        with allure.step("3. 校验响应是组织列表"):
            response_json = response.json()

            assert isinstance(response_json, list), (
                f"组织列表响应类型错误，实际响应: {response_json}"
            )

            assert len(response_json) > 0, "当前用户没有任何所属组织"

        with allure.step("4. 校验组织对象核心字段"):
            assert_json_has_keys(
                response_json[0],
                [
                    "id",
                    "name"
                ]
            )

    @allure.story("创建知识库")
    @allure.title("登录后创建知识库成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_create_knowledge_base_success(self, logged_in_api_client, organization_id):
        """
        测试登录后创建知识库成功
        """

        with allure.step("1. 读取 YAML 中的创建知识库测试数据"):
            case = load_yaml("knowledge_base_cases.yaml")["create_success"]

            payload = {
                "organization_id": organization_id,
                "name": case["name"],
                "description": case["description"]
            }

            allure.attach(
                str(payload),
                name="创建知识库请求数据",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("2. 调用创建知识库接口"):
            response = logged_in_api_client.create_knowledge_base(payload)
            attach_response(response, "创建知识库接口响应")

        with allure.step("3. 校验接口状态码"):
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验知识库响应字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "id",
                    "organization_id",
                    "name",
                    "description"
                ]
            )

        with allure.step("5. 校验知识库名称和组织 ID"):
            assert_value_equal(
                response_json["name"],
                case["name"],
                "name"
            )

            assert_value_equal(
                response_json["organization_id"],
                organization_id,
                "organization_id"
            )

    @allure.story("知识库列表")
    @allure.title("登录后查询知识库列表成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_list_knowledge_bases_success(self, logged_in_api_client, created_knowledge_base):
        """
        测试登录后查询知识库列表成功
        """

        with allure.step("1. 获取 fixture 创建的知识库 ID"):
            knowledge_base_id = created_knowledge_base["id"]

            allure.attach(
                str(created_knowledge_base),
                name="fixture 创建的知识库数据",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("2. 调用知识库列表接口"):
            response = logged_in_api_client.list_knowledge_bases()
            attach_response(response, "知识库列表接口响应")

        with allure.step("3. 校验接口状态码"):
            case = load_yaml("knowledge_base_cases.yaml")["list_success"]
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验刚创建的知识库存在于列表中"):
            response_json = response.json()

            assert isinstance(response_json, list), (
                f"知识库列表响应类型错误，实际响应: {response_json}"
            )

            knowledge_base_ids = [item["id"] for item in response_json]

            assert knowledge_base_id in knowledge_base_ids, (
                f"知识库列表中未找到刚创建的知识库，"
                f"期望 ID: {knowledge_base_id}, "
                f"实际 ID 列表: {knowledge_base_ids}"
            )

    @allure.story("知识库详情")
    @allure.title("登录后查询知识库详情成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_get_knowledge_base_detail_success(self, logged_in_api_client, created_knowledge_base):
        """
        测试登录后查询知识库详情成功
        """

        with allure.step("1. 获取 fixture 创建的知识库 ID"):
            knowledge_base_id = created_knowledge_base["id"]

        with allure.step("2. 调用知识库详情接口"):
            response = logged_in_api_client.get_knowledge_base(knowledge_base_id)
            attach_response(response, "知识库详情接口响应")

        with allure.step("3. 校验接口状态码"):
            case = load_yaml("knowledge_base_cases.yaml")["detail_success"]
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验知识库详情字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "id",
                    "organization_id",
                    "name",
                    "description"
                ]
            )

        with allure.step("5. 校验返回的知识库 ID 正确"):
            assert_value_equal(
                response_json["id"],
                knowledge_base_id,
                "id"
            )

    @allure.story("权限校验")
    @allure.title("未登录创建知识库失败")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_create_knowledge_base_without_token(self, client):
        """
        测试未登录时创建知识库失败
        """

        with allure.step("1. 准备未登录创建知识库请求数据"):
            case = load_yaml("knowledge_base_cases.yaml")["create_without_token"]

            payload = {
                "organization_id": 1,
                "name": case["name"],
                "description": case["description"]
            }

        with allure.step("2. 不携带 token 调用创建知识库接口"):
            response = client.post(
                "/api/knowledge-bases",
                json=payload
            )
            attach_response(response, "未登录创建知识库接口响应")

        with allure.step("3. 校验接口返回 401"):
            assert_status_code(response, case["expected_status"])