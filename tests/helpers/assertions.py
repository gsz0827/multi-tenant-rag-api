import json
import allure

def attach_response(response, name: str = "接口响应"):
    """
    将接口响应内容附加到 Allure 报告中

    参数：
        response: 接口响应对象
        name: Allure 附件名称
    """

    try:
        # 尝试把响应内容格式化为 JSON，报告里更好看
        content = json.dumps(
            response.json(),
            ensure_ascii=False,
            indent=2
        )
    except Exception:
        # 如果响应不是 JSON，就直接使用文本内容
        content = response.text

    allure.attach(
        content,
        name=name,
        attachment_type=allure.attachment_type.JSON
    )
    

def assert_status_code(response, expected_status_code: int):
    """
    断言接口响应状态码

    参数：
        response: 接口响应对象
        expected_status_code: 期望状态码
    """

    assert response.status_code == expected_status_code, (
        f"\n状态码断言失败"
        f"\n期望状态码: {expected_status_code}"
        f"\n实际状态码: {response.status_code}"
        f"\n响应内容: {response.text}"
    )


def assert_json_has_keys(response_json: dict, expected_keys: list):
    """
    断言响应 JSON 中包含指定字段

    参数：
        response_json: 接口返回的 JSON 数据
        expected_keys: 期望存在的字段列表
    """

    for key in expected_keys:
        assert key in response_json, (
            f"\n响应 JSON 缺少字段: {key}"
            f"\n实际响应 JSON: {response_json}"
        )


def assert_value_equal(actual, expected, field_name: str = ""):
    """
    断言实际值和期望值相等

    参数：
        actual: 实际值
        expected: 期望值
        field_name: 字段名称，用于错误提示
    """

    assert actual == expected, (
        f"\n字段断言失败: {field_name}"
        f"\n期望值: {expected}"
        f"\n实际值: {actual}"
    )


def assert_response_time(response, max_ms: int = 1000):
    """
    断言接口响应时间

    参数：
        response: 接口响应对象
        max_ms: 最大允许响应时间，单位毫秒

    注意：
        FastAPI TestClient 的响应对象默认不一定有 elapsed，
        这个方法后面做真实 requests/httpx 测试时会更常用。
    """

    if not hasattr(response, "elapsed"):
        return

    elapsed_ms = response.elapsed.total_seconds() * 1000

    assert elapsed_ms <= max_ms, (
        f"\n接口响应时间过长"
        f"\n期望小于: {max_ms} ms"
        f"\n实际耗时: {elapsed_ms:.2f} ms"
    )