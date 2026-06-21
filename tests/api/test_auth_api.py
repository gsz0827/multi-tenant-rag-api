import pytest
import allure

from tests.helpers.assertions import (
    assert_status_code,
    assert_json_has_keys,
    assert_value_equal,
    attach_response,
)


@allure.epic("多租户 RAG 系统")
@allure.feature("用户认证模块")
class TestAuthApi:
    """
    用户认证接口测试

    覆盖范围：
    1. 用户注册
    2. 用户登录
    3. 获取当前用户信息
    """

    @allure.story("用户注册")
    @allure.title("用户注册成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_register_success(self, api_client, user_payload):
        """
        测试用户注册成功
        """

        with allure.step("1. 准备注册用户数据"):
            allure.attach(
                str(user_payload),
                name="注册请求数据",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("2. 发送用户注册请求"):
            response = api_client.register(user_payload)
            attach_response(response, "注册接口响应")

        with allure.step("3. 校验注册接口状态码"):
            assert_status_code(response, 200)

        with allure.step("4. 校验注册响应字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "id",
                    "email",
                    "username",
                    "full_name"
                ]
            )

        with allure.step("5. 校验返回邮箱与请求邮箱一致"):
            assert_value_equal(
                response_json["email"],
                user_payload["email"],
                "email"
            )

    @allure.story("用户登录")
    @allure.title("用户登录成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_login_success(self, api_client, registered_user):
        """
        测试用户登录成功
        """

        with allure.step("1. 使用已注册用户进行登录"):
            response = api_client.login(
                username=registered_user["email"],
                password=registered_user["password"]
            )
            attach_response(response, "登录接口响应")

        with allure.step("2. 校验登录接口状态码"):
            assert_status_code(response, 200)

        with allure.step("3. 校验 token 字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "access_token",
                    "token_type"
                ]
            )

        with allure.step("4. 校验 token 类型"):
            assert_value_equal(
                response_json["token_type"],
                "bearer",
                "token_type"
            )

    @allure.story("当前用户")
    @allure.title("登录后获取当前用户信息成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    @pytest.mark.smoke
    def test_get_current_user_success(self, logged_in_api_client):
        """
        测试登录后获取当前用户信息
        """

        with allure.step("1. 使用已登录客户端请求当前用户接口"):
            response = logged_in_api_client.get_current_user()
            attach_response(response, "当前用户接口响应")

        with allure.step("2. 校验接口状态码"):
            assert_status_code(response, 200)

        with allure.step("3. 校验用户信息字段"):
            response_json = response.json()

            assert_json_has_keys(
                response_json,
                [
                    "id",
                    "email",
                    "username"
                ]
            )