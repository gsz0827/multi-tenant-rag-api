import { useEffect, useMemo, useState } from "react";
import {
  cancelBatchIngestion,
  cancelDocumentIngestion,
  deleteDocument,
  getBatchIngestionStatus,
  listDocuments,
  listKnowledgeBases,
  login,
  prepareBatchAsync,
  prepareDocumentAsync,
  retryBatchIngestion,
  retryDocumentIngestion,
  uploadDocument,
} from "./api";
import "./App.css";

type KnowledgeBase = {
  id: number;
  name: string;
  description?: string | null;
};

type DocumentItem = {
  id: number;
  filename: string;
  content_type?: string | null;
  file_size?: number | null;
  status: string;
  task_id?: string | null;
  error_message?: string | null;
  created_at?: string;
};

type BatchStatusItem = {
  document_id: number;
  filename: string;
  document_status: string;
  celery_status?: string | null;
  task_id?: string | null;
  error_message?: string | null;
};

type BatchStatus = {
  knowledge_base_id: number;
  total_count: number;
  pending_count: number;
  queued_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  cancelled_count: number;
  results: BatchStatusItem[];
};

const runningStatuses = new Set(["queued", "processing"]);
const retryableStatuses = new Set(["pending", "failed", "cancelled"]);

function statusLabel(status: string) {
  const className = `status status-${status}`;
  return <span className={className}>{status}</span>;
}

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState<number | null>(null);

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const isLoggedIn = useMemo(() => {
    return Boolean(localStorage.getItem("access_token"));
  }, [message]);

  async function refreshKnowledgeBases() {
    const data = await listKnowledgeBases();
    setKnowledgeBases(data);

    if (data.length > 0 && knowledgeBaseId === null) {
      setKnowledgeBaseId(data[0].id);
    }
  }

  async function refreshDocuments(targetKnowledgeBaseId = knowledgeBaseId) {
    if (!targetKnowledgeBaseId) return;

    const data = await listDocuments(targetKnowledgeBaseId);
    setDocuments(data);
  }

  async function refreshBatchStatus(targetKnowledgeBaseId = knowledgeBaseId) {
    if (!targetKnowledgeBaseId) return;

    const data = await getBatchIngestionStatus(targetKnowledgeBaseId);
    setBatchStatus(data);
  }

  async function refreshAll(targetKnowledgeBaseId = knowledgeBaseId) {
    await refreshDocuments(targetKnowledgeBaseId);
    await refreshBatchStatus(targetKnowledgeBaseId);
  }

  async function handleLogin() {
    try {
      setLoading(true);
      await login(email, password);
      setMessage("登录成功");
      await refreshKnowledgeBases();
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || "登录失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload() {
    if (!knowledgeBaseId || !selectedFile) {
      setMessage("请先选择知识库和文件");
      return;
    }

    try {
      setLoading(true);
      await uploadDocument(knowledgeBaseId, selectedFile);
      setSelectedFile(null);
      setMessage("上传成功");
      await refreshAll(knowledgeBaseId);
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || "上传失败");
    } finally {
      setLoading(false);
    }
  }

  async function runAction(action: () => Promise<any>, successMessage: string) {
    try {
      setLoading(true);
      await action();
      setMessage(successMessage);
      await refreshAll();
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || "操作失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (localStorage.getItem("access_token")) {
      refreshKnowledgeBases().catch(() => {
        setMessage("获取知识库失败，请重新登录");
      });
    }
  }, []);

  useEffect(() => {
    if (knowledgeBaseId) {
      refreshAll(knowledgeBaseId);
    }
  }, [knowledgeBaseId]);

  useEffect(() => {
    if (!knowledgeBaseId) return;

    const timer = window.setInterval(() => {
      refreshBatchStatus(knowledgeBaseId).catch(() => {});
      refreshDocuments(knowledgeBaseId).catch(() => {});
    }, 3000);

    return () => window.clearInterval(timer);
  }, [knowledgeBaseId]);

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>文档管理</h1>
          <p>上传文档、查看入库状态、执行单文档和批量操作。</p>
        </div>
        <button
          onClick={() => refreshAll()}
          disabled={!knowledgeBaseId || loading}
        >
          刷新
        </button>
      </header>

      {!isLoggedIn && (
        <section className="card">
          <h2>登录</h2>
          <div className="form-row">
            <input
              placeholder="邮箱"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <input
              placeholder="密码"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button onClick={handleLogin} disabled={loading}>
              登录
            </button>
          </div>
        </section>
      )}

      <section className="card">
        <h2>知识库</h2>
        <div className="form-row">
          <select
            value={knowledgeBaseId ?? ""}
            onChange={(event) => setKnowledgeBaseId(Number(event.target.value))}
          >
            <option value="" disabled>
              请选择知识库
            </option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name} #{kb.id}
              </option>
            ))}
          </select>
          <button onClick={refreshKnowledgeBases} disabled={loading}>
            重新加载知识库
          </button>
        </div>
      </section>

      {batchStatus && (
        <section className="stats">
          <div>总数：{batchStatus.total_count}</div>
          <div>pending：{batchStatus.pending_count}</div>
          <div>queued：{batchStatus.queued_count}</div>
          <div>processing：{batchStatus.processing_count}</div>
          <div>completed：{batchStatus.completed_count}</div>
          <div>failed：{batchStatus.failed_count}</div>
          <div>cancelled：{batchStatus.cancelled_count}</div>
        </section>
      )}

      <section className="card">
        <h2>上传文档</h2>
        <div className="form-row">
          <input
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={(event) => {
              setSelectedFile(event.target.files?.[0] ?? null);
            }}
          />
          <button onClick={handleUpload} disabled={loading || !selectedFile}>
            上传
          </button>
        </div>
      </section>

      <section className="card">
        <h2>批量操作</h2>
        <div className="button-row">
          <button
            disabled={!knowledgeBaseId || loading}
            onClick={() =>
              runAction(
                () => prepareBatchAsync(knowledgeBaseId!, false),
                "批量入库任务已提交"
              )
            }
          >
            批量入库
          </button>
          <button
            disabled={!knowledgeBaseId || loading}
            onClick={() =>
              runAction(
                () => cancelBatchIngestion(knowledgeBaseId!),
                "批量取消已提交"
              )
            }
          >
            批量取消
          </button>
          <button
            disabled={!knowledgeBaseId || loading}
            onClick={() =>
              runAction(
                () => retryBatchIngestion(knowledgeBaseId!, true),
                "批量重试已提交"
              )
            }
          >
            批量重试
          </button>
        </div>
      </section>

      {message && <div className="message">{message}</div>}

      <section className="card">
        <h2>文档列表</h2>

        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>文件名</th>
              <th>状态</th>
              <th>Task ID</th>
              <th>错误</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.id}</td>
                <td>{doc.filename}</td>
                <td>{statusLabel(doc.status)}</td>
                <td className="task-id">{doc.task_id || "-"}</td>
                <td className="error">{doc.error_message || "-"}</td>
                <td>
                  <div className="button-row">
                    <button
                      disabled={loading || runningStatuses.has(doc.status)}
                      onClick={() =>
                        runAction(
                          () => prepareDocumentAsync(doc.id, false),
                          "单文档入库任务已提交"
                        )
                      }
                    >
                      入库
                    </button>

                    <button
                      disabled={loading || !runningStatuses.has(doc.status)}
                      onClick={() =>
                        runAction(
                          () => cancelDocumentIngestion(doc.id),
                          "单文档取消已提交"
                        )
                      }
                    >
                      取消
                    </button>

                    <button
                      disabled={loading || !retryableStatuses.has(doc.status)}
                      onClick={() =>
                        runAction(
                          () => retryDocumentIngestion(doc.id, true),
                          "单文档重试已提交"
                        )
                      }
                    >
                      重试
                    </button>

                    <button
                      disabled={loading}
                      onClick={() =>
                        runAction(
                          () => deleteDocument(doc.id),
                          "文档已删除"
                        )
                      }
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}

            {documents.length === 0 && (
              <tr>
                <td colSpan={6} className="empty">
                  暂无文档
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}

export default App;