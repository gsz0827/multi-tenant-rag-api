import pytest
import allure

from tests.helpers.yaml_loader import load_yaml
from tests.helpers.assertions import (
    assert_status_code,
    assert_json_has_keys,
    attach_response,
)


@allure.epic("多租户 RAG 系统")
@allure.feature("RAG 问答模块")
class TestRagApi:
    """
    RAG 问答接口测试

    覆盖范围：
    1. 未登录访问 RAG 问答失败
    2. answer_language 参数非法失败
    3. 知识库没有 embedded chunks 时问答失败
    """

    @allure.story("权限校验")
    @allure.title("未登录访问 RAG 问答接口失败")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_ask_rag_without_token_failed(self, client, created_knowledge_base):
        """
        测试未登录访问 RAG 问答接口失败

        说明：
        这里故意使用普通 client，
        不使用 logged_in_api_client，
        所以请求不会携带 token。
        """

        with allure.step("1. 准备未登录 RAG 问答请求数据"):
            case = load_yaml("rag_cases.yaml")["ask_without_token"]

            payload = {
                "knowledge_base_id": created_knowledge_base["id"],
                "question": case["question"],
                "top_k": case["top_k"],
                "answer_language": case["answer_language"]
            }

            allure.attach(
                str(payload),
                name="未登录 RAG 请求数据",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("2. 不携带 token 调用 RAG 问答接口"):
            response = client.post(
                "/api/rag/ask",
                json=payload
            )
            attach_response(response, "未登录 RAG 问答接口响应")

        with allure.step("3. 校验接口返回 401"):
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验错误响应中包含 detail"):
            response_json = response.json()
            assert_json_has_keys(response_json, ["detail"])

    @allure.story("参数校验")
    @allure.title("answer_language 参数非法时返回 400")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_ask_rag_invalid_answer_language_failed(self, logged_in_api_client, created_knowledge_base):
        """
        测试 answer_language 参数非法时返回 400

        当前后端只允许：
        auto / zh / en
        """

        with allure.step("1. 准备非法 answer_language 请求数据"):
            case = load_yaml("rag_cases.yaml")["ask_invalid_answer_language"]

            payload = {
                "knowledge_base_id": created_knowledge_base["id"],
                "question": case["question"],
                "top_k": case["top_k"],
                "answer_language": case["answer_language"]
            }

            allure.attach(
                str(payload),
                name="非法 answer_language 请求数据",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("2. 调用 RAG 问答接口"):
            response = logged_in_api_client.ask_rag(payload)
            attach_response(response, "非法 answer_language 接口响应")

        with allure.step("3. 校验接口返回 400"):
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验错误响应内容"):
            response_json = response.json()
            assert_json_has_keys(response_json, ["detail"])

            assert "answer_language" in str(response_json["detail"])

    @allure.story("无可检索内容")
    @allure.title("知识库没有 embedded chunks 时 RAG 问答返回 404")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_ask_rag_no_embedded_chunks_failed(self, logged_in_api_client, created_knowledge_base):
        """
        测试知识库没有 embedded chunks 时，RAG 问答返回 404

        说明：
        这个用例创建了知识库，但没有插入 DocumentChunk embedding 数据。
        所以后端检索不到可用 chunk，应该返回 404。
        """

        with allure.step("1. 准备无 embedded chunks 的 RAG 请求数据"):
            case = load_yaml("rag_cases.yaml")["ask_no_embedded_chunks"]

            payload = {
                "knowledge_base_id": created_knowledge_base["id"],
                "question": case["question"],
                "top_k": case["top_k"],
                "answer_language": case["answer_language"]
            }

            allure.attach(
                str(payload),
                name="无 embedded chunks RAG 请求数据",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("2. 调用 RAG 问答接口"):
            response = logged_in_api_client.ask_rag(payload)
            attach_response(response, "无 embedded chunks RAG 接口响应")

        with allure.step("3. 校验接口返回 404"):
            assert_status_code(response, case["expected_status"])

        with allure.step("4. 校验错误响应中包含 detail"):
            response_json = response.json()
            assert_json_has_keys(response_json, ["detail"])