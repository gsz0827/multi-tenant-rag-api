import { useEffect, useState } from "react";
import {
  askKnowledgeBase,
  cancelBatchIngestion,
  cancelDocumentIngestion,
  clearAccessToken,
  createKnowledgeBase,
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

type RagSource = {
  document_id: number;
  filename: string;
  chunk_id: number;
  chunk_index: number;
  content: string;
  score: number;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sources?: RagSource[];
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

  const [newKbOrganizationId, setNewKbOrganizationId] = useState("1");
  const [newKbName, setNewKbName] = useState("");
  const [newKbDescription, setNewKbDescription] = useState("");

  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return Boolean(localStorage.getItem("access_token"));
  });

  const [question, setQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

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
      setIsLoggedIn(true);
      setMessage("登录成功");
    } catch (error: any) {
      setIsLoggedIn(false);
      setMessage(error?.response?.data?.detail || "登录失败");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    clearAccessToken();
    setIsLoggedIn(false);
    setKnowledgeBases([]);
    setKnowledgeBaseId(null);
    setDocuments([]);
    setBatchStatus(null);
    setSelectedFile(null);
    setQuestion("");
    setChatMessages([]);
    setEmail("");
    setPassword("");
    setMessage("已退出登录");
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

  async function handleAskQuestion() {
    if (!knowledgeBaseId) {
      setMessage("请先选择知识库");
      return;
    }

    const cleanQuestion = question.trim();

    if (!cleanQuestion) {
      setMessage("请输入问题");
      return;
    }

    try {
      setChatLoading(true);

      setChatMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: cleanQuestion,
        },
      ]);

      setQuestion("");

      const data = await askKnowledgeBase({
        knowledge_base_id: knowledgeBaseId,
        question: cleanQuestion,
        top_k: 5,
        answer_language: "auto",
      });

      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        },
      ]);
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || "问答失败");
    } finally {
      setChatLoading(false);
    }
  }

  async function handleCreateKnowledgeBase() {
    const organizationId = Number(newKbOrganizationId);

    if (!organizationId || !newKbName.trim()) {
      setMessage("请填写组织 ID 和知识库名称");
      return;
    }

    try {
      setLoading(true);

      const createdKnowledgeBase = await createKnowledgeBase({
        organization_id: organizationId,
        name: newKbName.trim(),
        description: newKbDescription.trim() || undefined,
      });

      setNewKbName("");
      setNewKbDescription("");
      setKnowledgeBaseId(createdKnowledgeBase.id);
      setMessage("知识库创建成功");

      await refreshKnowledgeBases();
      await refreshAll(createdKnowledgeBase.id);
    } catch (error: any) {
      setMessage(error?.response?.data?.detail || "创建知识库失败");
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
    if (!isLoggedIn) return;

    refreshKnowledgeBases().catch(() => {
      clearAccessToken();
      setIsLoggedIn(false);
      setMessage("登录已失效，请重新登录");
    });
  }, [isLoggedIn]);

  useEffect(() => {
    if (isLoggedIn && knowledgeBaseId) {
      refreshAll(knowledgeBaseId);
    }
  }, [isLoggedIn, knowledgeBaseId]);

  useEffect(() => {
    if (!isLoggedIn || !knowledgeBaseId) return;

    const timer = window.setInterval(() => {
      refreshBatchStatus(knowledgeBaseId).catch(() => {});
      refreshDocuments(knowledgeBaseId).catch(() => {});
    }, 3000);

    return () => window.clearInterval(timer);
  }, [isLoggedIn, knowledgeBaseId]);

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>文档管理</h1>
          <p>上传文档、查看入库状态、执行单文档和批量操作。</p>
        </div>
        <div className="button-row">
          {isLoggedIn && (
            <button
              onClick={() => refreshAll()}
              disabled={!knowledgeBaseId || loading}
            >
              刷新
            </button>
          )}

          {isLoggedIn && (
            <button onClick={handleLogout} disabled={loading}>
              退出登录
            </button>
          )}
        </div>
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

      {message && <div className="message">{message}</div>}

      {isLoggedIn && (
        <>
          <section className="card">
            <h2>知识库</h2>

            <div className="form-row">
              <select
                value={knowledgeBaseId ?? ""}
                onChange={(event) => {
                  setKnowledgeBaseId(Number(event.target.value));
                  setQuestion("");
                  setChatMessages([]);
                }}
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

            <div className="divider" />

            <h3 className="sub-title">创建知识库</h3>

            <div className="form-row">
              <input
                placeholder="组织 ID，例如 1"
                value={newKbOrganizationId}
                onChange={(event) => setNewKbOrganizationId(event.target.value)}
              />

              <input
                placeholder="知识库名称"
                value={newKbName}
                onChange={(event) => setNewKbName(event.target.value)}
              />

              <input
                placeholder="描述，可选"
                value={newKbDescription}
                onChange={(event) => setNewKbDescription(event.target.value)}
              />

              <button onClick={handleCreateKnowledgeBase} disabled={loading}>
                创建知识库
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
          
          <section className="card">
            <h2>知识库问答</h2>

            <div className="chat-box">
              {chatMessages.length === 0 && (
                <div className="empty">
                  请选择一个已完成入库的知识库，然后输入问题。
                </div>
              )}

              {chatMessages.map((item, index) => (
                <div key={index} className={`chat-message chat-${item.role}`}>
                  <div className="chat-role">
                    {item.role === "user" ? "我" : "助手"}
                  </div>

                  <div className="chat-content">{item.content}</div>

                  {item.sources && item.sources.length > 0 && (
                    <div className="source-list">
                      <div className="source-title">引用来源</div>

                      {item.sources.map((source, sourceIndex) => (
                        <details key={source.chunk_id} className="source-item">
                          <summary>
                            [{sourceIndex + 1}] {source.filename} ｜ chunk #
                            {source.chunk_index} ｜ score {source.score.toFixed(3)}
                          </summary>
                          <pre>{source.content}</pre>
                        </details>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="chat-input-row">
              <textarea
                placeholder="请输入你的问题，例如：这份文档主要讲了什么？"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                    handleAskQuestion();
                  }
                }}
              />

              <button
                onClick={handleAskQuestion}
                disabled={!knowledgeBaseId || chatLoading || !question.trim()}
              >
                {chatLoading ? "回答中..." : "发送"}
              </button>
            </div>

            <p className="hint">快捷键：Ctrl + Enter 发送</p>
          </section>
        </>
      )}
    </main>
  );
}

export default App;