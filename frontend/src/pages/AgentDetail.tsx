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
  Spin,
  Table,
  Typography,
} from "antd";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getAgent, inviteMember, listMembers, removeMember } from "../api/agents";
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
  const [inviteForm] = Form.useForm<{ user_id: string }>();
  const [versionForm] = Form.useForm<{ url?: string }>();

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
          <Typography.Paragraph type="secondary" style={{ marginBottom: 16 }}>
            這會建立一個草稿版本，之後可以在版本詳情頁自由編輯 URL、streaming、依賴等參數，
            直到你自己按下「送審」才會正式送出去審核。
          </Typography.Paragraph>
          <Form.Item label="Endpoint URL" name="url" extra="之後可以在版本詳情頁繼續編輯其他參數">
            <Input placeholder="https://agents.example.com/your-agent" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
