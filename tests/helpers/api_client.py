from pathlib import Path

class ApiClient:
    """
    API 请求封装类

    作用：
    1. 统一封装接口请求
    2. 统一管理登录 token
    3. 避免测试用例里重复写 client.get/client.post
    """

    def __init__(self, client):
        # FastAPI TestClient 对象
        self.client = client

        # 登录成功后保存 JWT token
        self.token = None

    def set_token(self, token: str):
        """
        设置登录 token
        """

        self.token = token

    @property
    def headers(self):
        """
        根据当前 token 自动生成请求头

        如果未登录，则返回空请求头
        如果已登录，则返回 Authorization 请求头
        """

        if not self.token:
            return {}

        return {
            "Authorization": f"Bearer {self.token}"
        }

    # ==============================
    # 认证模块接口
    # ==============================

    def register(self, payload: dict):
        """
        用户注册接口

        payload 示例：
        {
            "email": "test@example.com",
            "username": "test_user",
            "full_name": "Test User",
            "password": "TestPassword123"
        }
        """

        return self.client.post(
            "/api/auth/register",
            json=payload
        )

    def login(self, username: str, password: str):
        """
        用户登录接口

        注意：
        登录接口通常使用 OAuth2PasswordRequestForm，
        所以这里使用 data，而不是 json。
        """

        return self.client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": password
            }
        )

    def get_current_user(self):
        """
        获取当前登录用户信息
        """

        return self.client.get(
            "/api/users/me",
            headers=self.headers
        )

    # ==============================
    # 组织模块接口
    # ==============================

    def list_organizations(self):
        """
        查询当前用户所属组织列表

        注意：
        后端 organizations 路由是 /organizations/me，
        加上 API_PREFIX 后完整路径是 /api/organizations/me
        """

        return self.client.get(
            "/api/organizations/me",
            headers=self.headers
        )

    # ==============================
    # 知识库模块接口
    # ==============================

    def create_knowledge_base(self, payload: dict):
        """
        创建知识库
        """

        return self.client.post(
            "/api/knowledge-bases",
            json=payload,
            headers=self.headers
        )

    def list_knowledge_bases(self):
        """
        查询知识库列表
        """

        return self.client.get(
            "/api/knowledge-bases",
            headers=self.headers
        )

    def get_knowledge_base(self, knowledge_base_id: int):
        """
        查询知识库详情
        """

        return self.client.get(
            f"/api/knowledge-bases/{knowledge_base_id}",
            headers=self.headers
        )

    def delete_knowledge_base(self, knowledge_base_id: int):
        """
        删除知识库
        """

        return self.client.delete(
            f"/api/knowledge-bases/{knowledge_base_id}",
            headers=self.headers
        )

    # ==============================
    # 文档模块接口
    # ==============================

    def upload_document(
        self,
        knowledge_base_id: int,
        file_path: str,
        content_type: str = "text/plain"
    ):
        """
        上传文档

        参数：
            knowledge_base_id: 知识库 ID
            file_path: 本地测试文件路径
            content_type: 文件类型，例如 text/plain

        说明：
            这里使用 Path(file_path).name 作为上传文件名，
            避免把完整本地路径传给后端。
        """

        # 获取文件名，例如 test_document.txt
        file_name = Path(file_path).name

        with open(file_path, "rb") as f:
            return self.client.post(
                "/api/documents/upload",
                data={
                    "knowledge_base_id": knowledge_base_id
                },
                files={
                    "file": (
                        file_name,
                        f,
                        content_type
                    )
                },
                headers=self.headers
            )

    def list_documents(self, knowledge_base_id: int):
        """
        查询某个知识库下的文档列表
        """

        return self.client.get(
            f"/api/documents?knowledge_base_id={knowledge_base_id}",
            headers=self.headers
        )

    def get_document(self, document_id: int):
        """
        查询文档详情
        """

        return self.client.get(
            f"/api/documents/{document_id}",
            headers=self.headers
        )

    def delete_document(self, document_id: int):
        """
        删除文档
        """

        return self.client.delete(
            f"/api/documents/{document_id}",
            headers=self.headers
        )
    
    # ==============================
    # RAG 问答模块接口
    # ==============================

    def ask_rag(self, payload: dict):
        """
        RAG 问答接口
        """

        return self.client.post(
            "/api/rag/ask",
            json=payload,
            headers=self.headers
        )