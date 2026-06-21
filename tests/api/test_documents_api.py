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
@allure.feature("文档管理模块")
class TestDocumentsApi:
    """
    文档接口测试

    覆盖范围：
    1. 上传 TXT 文档
    2. 查询文档列表
    3. 查询文档详情
    4. 上传不支持的文件类型
    5. 未登录上传文档
    """

    @allure.story("文档上传")
    @allure.title("登录后上传 TXT 文档成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_upload_txt_document_success(self, logged_in_api_client, created_knowledge_base, tmp_path):
        """
        测试登录后上传 TXT 文档成功
        """

        with allure.step("1. 读取 YAML 中的 TXT 上传测试数据"):
            case = load_yaml("document_cases.yaml")["txt_upload_success"]
            knowledge_base_id = created_knowledge_base["id"]

        with allure.step("2. 在 pytest 临时目录中创建 TXT 测试文件"):
            test_file = tmp_path / case["file_name"]
            test_file.write_text(case["content"], encoding="utf-8")

            allure.attach(
                case["content"],
                name="上传的 TXT 文档内容",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("3. 调用文档上传接口"):
            response = logged_in_api_client.upload_document(
                knowledge_base_id=knowledge_base_id,
                file_path=str(test_file),
                content_type=case["content_type"]
            )
            attach_response(response, "文档上传接口响应")

        with allure.step("4. 校验接口状态码"):
            assert_status_code(response, case["expected_status"])

        with allure.step("5. 校验上传响应字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "id",
                    "knowledge_base_id",
                    "filename",
                    "content_type",
                    "file_size",
                    "status"
                ]
            )

        with allure.step("6. 校验文件归属知识库、文件名和文件类型"):
            assert_value_equal(
                response_json["knowledge_base_id"],
                knowledge_base_id,
                "knowledge_base_id"
            )

            assert_value_equal(
                response_json["filename"],
                case["file_name"],
                "filename"
            )

            assert_value_equal(
                response_json["content_type"],
                case["content_type"],
                "content_type"
            )

    @allure.story("文档列表")
    @allure.title("登录后查询文档列表成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_list_documents_success(self, logged_in_api_client, created_knowledge_base, tmp_path):
        """
        测试登录后查询知识库下的文档列表
        """

        with allure.step("1. 准备文档上传数据"):
            upload_case = load_yaml("document_cases.yaml")["txt_upload_success"]
            list_case = load_yaml("document_cases.yaml")["list_success"]
            knowledge_base_id = created_knowledge_base["id"]

            test_file = tmp_path / upload_case["file_name"]
            test_file.write_text(upload_case["content"], encoding="utf-8")

        with allure.step("2. 先上传一个文档，保证列表中存在数据"):
            upload_response = logged_in_api_client.upload_document(
                knowledge_base_id=knowledge_base_id,
                file_path=str(test_file),
                content_type=upload_case["content_type"]
            )
            attach_response(upload_response, "前置上传文档接口响应")

            assert_status_code(upload_response, upload_case["expected_status"])

            uploaded_document_id = upload_response.json()["id"]

        with allure.step("3. 调用文档列表接口"):
            response = logged_in_api_client.list_documents(knowledge_base_id)
            attach_response(response, "文档列表接口响应")

        with allure.step("4. 校验接口状态码"):
            assert_status_code(response, list_case["expected_status"])

        with allure.step("5. 校验刚上传的文档存在于列表中"):
            response_json = response.json()

            assert isinstance(response_json, list), (
                f"文档列表响应类型错误，实际响应: {response_json}"
            )

            document_ids = [item["id"] for item in response_json]

            assert uploaded_document_id in document_ids, (
                f"文档列表中未找到刚上传的文档，"
                f"期望文档 ID: {uploaded_document_id}, "
                f"实际文档 ID 列表: {document_ids}"
            )

    @allure.story("文档详情")
    @allure.title("登录后查询文档详情成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_get_document_detail_success(self, logged_in_api_client, created_knowledge_base, tmp_path):
        """
        测试登录后查询文档详情成功
        """

        with allure.step("1. 准备并上传测试文档"):
            upload_case = load_yaml("document_cases.yaml")["txt_upload_success"]
            detail_case = load_yaml("document_cases.yaml")["detail_success"]
            knowledge_base_id = created_knowledge_base["id"]

            test_file = tmp_path / upload_case["file_name"]
            test_file.write_text(upload_case["content"], encoding="utf-8")

            upload_response = logged_in_api_client.upload_document(
                knowledge_base_id=knowledge_base_id,
                file_path=str(test_file),
                content_type=upload_case["content_type"]
            )
            attach_response(upload_response, "前置上传文档接口响应")

            assert_status_code(upload_response, upload_case["expected_status"])

            uploaded_document = upload_response.json()
            document_id = uploaded_document["id"]

        with allure.step("2. 调用文档详情接口"):
            response = logged_in_api_client.get_document(document_id)
            attach_response(response, "文档详情接口响应")

        with allure.step("3. 校验接口状态码"):
            assert_status_code(response, detail_case["expected_status"])

        with allure.step("4. 校验文档详情字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "id",
                    "knowledge_base_id",
                    "filename",
                    "content_type",
                    "file_size",
                    "status"
                ]
            )

        with allure.step("5. 校验文档 ID 和文件名正确"):
            assert_value_equal(
                response_json["id"],
                document_id,
                "id"
            )

            assert_value_equal(
                response_json["filename"],
                upload_case["file_name"],
                "filename"
            )

    @allure.story("文件类型校验")
    @allure.title("上传不支持的文件类型失败")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_upload_unsupported_file_type_failed(self, logged_in_api_client, created_knowledge_base, tmp_path):
        """
        测试上传不支持的文件类型失败
        """

        with allure.step("1. 准备不支持的文件类型测试数据"):
            case = load_yaml("document_cases.yaml")["unsupported_file_type"]
            knowledge_base_id = created_knowledge_base["id"]

            test_file = tmp_path / case["file_name"]
            test_file.write_text(case["content"], encoding="utf-8")

        with allure.step("2. 调用文档上传接口"):
            response = logged_in_api_client.upload_document(
                knowledge_base_id=knowledge_base_id,
                file_path=str(test_file),
                content_type=case["content_type"]
            )
            attach_response(response, "上传不支持文件类型接口响应")

        with allure.step("3. 校验接口返回 400"):
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验错误响应中包含 detail"):
            response_json = response.json()
            assert_json_has_keys(response_json, ["detail"])

    @allure.story("权限校验")
    @allure.title("未登录上传文档失败")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_upload_document_without_token_failed(self, client, created_knowledge_base, tmp_path):
        """
        测试未登录上传文档失败
        """

        with allure.step("1. 准备未登录上传文档测试数据"):
            case = load_yaml("document_cases.yaml")["upload_without_token"]
            knowledge_base_id = created_knowledge_base["id"]

            test_file = tmp_path / case["file_name"]
            test_file.write_text(case["content"], encoding="utf-8")

        with allure.step("2. 不携带 token 直接上传文档"):
            with open(test_file, "rb") as f:
                response = client.post(
                    "/api/documents/upload",
                    data={
                        "knowledge_base_id": knowledge_base_id
                    },
                    files={
                        "file": (
                            case["file_name"],
                            f,
                            case["content_type"]
                        )
                    }
                )

            attach_response(response, "未登录上传文档接口响应")

        with allure.step("3. 校验接口返回 401"):
            assert_status_code(response, case["expected_status"])