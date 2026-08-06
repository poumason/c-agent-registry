import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App,
  Avatar,
  Breadcrumb,
  Button,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Spin,
  Table,
  Typography,
} from "antd";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteAgent,
  getAgent,
  inviteMember,
  listMembers,
  removeMember,
  updateAgent,
} from "../api/agents";
import type { UpdateAgentInput } from "../api/agents";
import type { AgentVersion } from "../api/types";
import { createVersion, listVersions } from "../api/versions";
import { AssetRoleTag, VersionStatusTag, VisibilityTag } from "../components/tags";

export default function AgentDetail() {
  const { message } = App.useApp();
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [newVersionOpen, setNewVersionOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [inviteForm] = Form.useForm<{ user_id: string }>();
  const [versionForm] = Form.useForm<{ url?: string }>();
  const [editForm] = Form.useForm<UpdateAgentInput>();

  const agentQuery = useQuery({
    queryKey: ["agent", slug],
    queryFn: () => getAgent(slug!),
    enabled: !!slug,
  });
  const versionsQuery = useQuery({
    queryKey: ["agent-versions", slug],
    queryFn: () => listVersions(slug!),
    enabled: !!slug,
  });
  const membersQuery = useQuery({
    queryKey: ["agent-members", slug],
    queryFn: () => listMembers(slug!),
    enabled: !!slug,
  });

  const inviteMutation = useMutation({
    mutationFn: (userId: string) => inviteMember(slug!, userId),
    onSuccess: () => {
      message.success("已邀請為 editor");
      queryClient.invalidateQueries({ queryKey: ["agent-members", slug] });
      setInviteOpen(false);
      inviteForm.resetFields();
    },
    onError: () => message.error("邀請失敗，請確認 user id 是否正確"),
  });

  const removeMutation = useMutation({
    mutationFn: (userId: string) => removeMember(slug!, userId),
    onSuccess: () => {
      message.success("已移除成員");
      queryClient.invalidateQueries({ queryKey: ["agent-members", slug] });
    },
    onError: () => message.error("移除失敗"),
  });

  const createVersionMutation = useMutation({
    mutationFn: (url?: string) => createVersion(slug!, { url }),
    onSuccess: (version) => {
      message.success("已建立草稿版本");
      queryClient.invalidateQueries({ queryKey: ["agent-versions", slug] });
      setNewVersionOpen(false);
      versionForm.resetFields();
      navigate(`/agents/${slug}/versions/${version.slug}`);
    },
    onError: () => message.error("建立版本失敗"),
  });

  const updateMutation = useMutation({
    mutationFn: (input: UpdateAgentInput) => updateAgent(slug!, input),
    onSuccess: () => {
      message.success("已更新 agent");
      queryClient.invalidateQueries({ queryKey: ["agent", slug] });
      setEditOpen(false);
    },
    onError: () => message.error("更新失敗"),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteAgent(slug!),
    onSuccess: () => {
      message.success("已刪除 agent");
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      navigate("/my-agents");
    },
    onError: () => message.error("刪除失敗"),
  });

  if (agentQuery.isLoading || !agentQuery.data) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }
  const agent = agentQuery.data;

  return (
    <div>
      <Breadcrumb
        items={[{ title: <Link to="/my-agents">Agents</Link> }, { title: agent.name }]}
        style={{ marginBottom: 8, fontSize: 12.5 }}
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 20, marginBottom: 22 }}>
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4, display: "flex", alignItems: "center", gap: 10 }}>
            {agent.name}
            <span style={{ fontFamily: "monospace", fontSize: 12.5, fontWeight: 500, color: "#9AA0AC" }}>
              {agent.slug}
            </span>
            <VisibilityTag visibility={agent.visibility} />
          </Typography.Title>
          {agent.description && (
            <Typography.Paragraph type="secondary" style={{ maxWidth: "60ch", marginBottom: 8 }}>
              {agent.description}
            </Typography.Paragraph>
          )}
          <div style={{ display: "flex", gap: 20, fontSize: 12.5, color: "#9AA0AC" }}>
            {agent.provider && (
              <div>
                Provider：<b style={{ color: "#6B7280" }}>{agent.provider}</b>
              </div>
            )}
            <div>
              建立於：<b style={{ color: "#6B7280" }}>{new Date(agent.created_at).toLocaleDateString()}</b>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
          <Button
            onClick={() => {
              editForm.setFieldsValue({
                name: agent.name,
                description: agent.description ?? undefined,
                provider: agent.provider ?? undefined,
                visibility: agent.visibility,
              });
              setEditOpen(true);
            }}
          >
            編輯
          </Button>
          <Popconfirm
            title="確定要刪除這個 agent 嗎？"
            description="刪除後會從列表消失，但版本/審核紀錄不會被清除。"
            onConfirm={() => deleteMutation.mutate()}
            okText="刪除"
            okButtonProps={{ danger: true }}
            cancelText="取消"
          >
            <Button danger loading={deleteMutation.isPending}>
              刪除
            </Button>
          </Popconfirm>
          <Button onClick={() => setInviteOpen(true)}>邀請成員</Button>
          <Button type="primary" onClick={() => setNewVersionOpen(true)}>
            新增版本
          </Button>
        </div>
      </div>

      <Table
        rowKey="slug"
        loading={versionsQuery.isLoading}
        dataSource={versionsQuery.data ?? []}
        pagination={false}
        onRow={(record: AgentVersion) => ({
          style: { cursor: "pointer" },
          onClick: () => navigate(`/agents/${slug}/versions/${record.slug}`),
        })}
        style={{ marginBottom: 28 }}
        locale={{ emptyText: "尚無版本，點右上角「新增版本」建立第一個草稿" }}
        columns={[
          { title: "版本", dataIndex: "version", render: (v: number) => `v${v}` },
          { title: "狀態", dataIndex: "status", render: (s: AgentVersion["status"]) => <VersionStatusTag status={s} /> },
          { title: "Streaming", dataIndex: "streaming", render: (v: boolean) => (v ? "是" : "否") },
          {
            title: "更新時間",
            dataIndex: "updated_at",
            render: (v: string) => new Date(v).toLocaleString(),
          },
        ]}
      />

      <Typography.Title level={5} style={{ marginBottom: 12 }}>
        成員
      </Typography.Title>
      {membersQuery.data && membersQuery.data.length > 0 ? (
        <div style={{ background: "#fff", border: "1px solid #E4E6EC", borderRadius: 8 }}>
          {membersQuery.data.map((m, idx) => (
            <div
              key={m.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "13px 18px",
                borderBottom: idx === membersQuery.data.length - 1 ? "none" : "1px solid #E4E6EC",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Avatar size={22} style={{ background: "#EEF0FE", color: "#4338CA", fontSize: 10 }}>
                  {m.user_id.slice(0, 1).toUpperCase()}
                </Avatar>
                <span style={{ fontSize: 12.5, fontFamily: "monospace", color: "#6B7280" }}>{m.user_id}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <AssetRoleTag role={m.role} />
                {m.role !== "owner" && (
                  <Popconfirm
                    title="確定要移除這個成員嗎？"
                    onConfirm={() => removeMutation.mutate(m.user_id)}
                    okText="移除"
                    cancelText="取消"
                  >
                    <Button size="small" type="text" danger>
                      移除
                    </Button>
                  </Popconfirm>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Empty description="尚無成員資料" />
      )}

      <Modal
        title="編輯 Agent"
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={() => editForm.submit()}
        confirmLoading={updateMutation.isPending}
        okText="儲存"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical" onFinish={(v) => updateMutation.mutate(v)}>
          <Form.Item label="名稱" name="name" rules={[{ required: true, message: "請輸入名稱" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item label="Provider" name="provider">
            <Input />
          </Form.Item>
          <Form.Item label="Visibility" name="visibility" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "private", label: "private — 只有成員看得到" },
                { value: "internal", label: "internal — 登入的使用者都看得到" },
                { value: "public", label: "public — 對外公開" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="邀請成員"
        open={inviteOpen}
        onCancel={() => setInviteOpen(false)}
        onOk={() => inviteForm.submit()}
        confirmLoading={inviteMutation.isPending}
        okText="邀請"
        cancelText="取消"
      >
        <Form form={inviteForm} layout="vertical" onFinish={(v) => inviteMutation.mutate(v.user_id)}>
          <Form.Item
            label="User ID"
            name="user_id"
            rules={[{ required: true, message: "請輸入 user id" }]}
            extra="邀請後對方會取得 editor 權限。可請 admin 在使用者管理頁查詢 user id。"
          >
            <Input placeholder="00000000-0000-0000-0000-000000000000" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新增版本"
        open={newVersionOpen}
        onCancel={() => setNewVersionOpen(false)}
        onOk={() => versionForm.submit()}
        confirmLoading={createVersionMutation.isPending}
        okText="建立草稿"
        cancelText="取消"
      >
        <Form form={versionForm} layout="vertical" onFinish={(v) => createVersionMutation.mutate(v.url)}>
          <Form.Item label="Endpoint URL" name="url" extra="之後可以在版本詳情頁繼續編輯其他參數">
            <Input placeholder="https://agents.example.com/your-agent" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
