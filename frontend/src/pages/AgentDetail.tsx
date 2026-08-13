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
import { useTranslation } from "react-i18next";
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
import AgentFormFields from "../components/AgentFormFields";
import { AssetRoleTag, VersionStatusTag, VisibilityTag } from "../components/tags";
import { useFormatters } from "../lib/relativeTime";

export default function AgentDetail() {
  const { t } = useTranslation();
  const { formatDate, formatDateTime } = useFormatters();
  const { message } = App.useApp();
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [inviteForm] = Form.useForm<{ user_id: string }>();
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
      message.success(t("agentDetail.inviteSuccess"));
      queryClient.invalidateQueries({ queryKey: ["agent-members", slug] });
      setInviteOpen(false);
      inviteForm.resetFields();
    },
    onError: () => message.error(t("agentDetail.inviteFailed")),
  });

  const removeMutation = useMutation({
    mutationFn: (userId: string) => removeMember(slug!, userId),
    onSuccess: () => {
      message.success(t("agentDetail.removeMemberSuccess"));
      queryClient.invalidateQueries({ queryKey: ["agent-members", slug] });
    },
    onError: () => message.error(t("common.removeFailed")),
  });

  const createVersionMutation = useMutation({
    mutationFn: () => createVersion(slug!),
    onSuccess: (version) => {
      message.success(t("agentDetail.createVersionSuccess"));
      queryClient.invalidateQueries({ queryKey: ["agent-versions", slug] });
      // Nothing left to fill in here anymore — deployment fabs, dependencies, and
      // agent card skills are all set on the version's own detail page now.
      navigate(`/agents/${slug}/versions/${version.slug}`);
    },
    onError: () => message.error(t("agentDetail.createVersionFailed")),
  });

  const updateMutation = useMutation({
    mutationFn: (input: UpdateAgentInput) => updateAgent(slug!, input),
    onSuccess: () => {
      message.success(t("agentDetail.updateSuccess"));
      queryClient.invalidateQueries({ queryKey: ["agent", slug] });
      setEditOpen(false);
    },
    onError: () => message.error(t("agentDetail.updateFailed")),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteAgent(slug!),
    onSuccess: () => {
      message.success(t("agentDetail.deleteSuccess"));
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      navigate("/my-agents");
    },
    onError: () => message.error(t("agentDetail.deleteFailed")),
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
            <span style={{ fontFamily: "monospace", fontSize: 12.5, fontWeight: 500, color: "var(--fg-subtle)" }}>
              {agent.slug}
            </span>
            <VisibilityTag visibility={agent.visibility} />
          </Typography.Title>
          {agent.description && (
            <Typography.Paragraph type="secondary" style={{ maxWidth: "60ch", marginBottom: 8 }}>
              {agent.description}
            </Typography.Paragraph>
          )}
          <div style={{ display: "flex", gap: 20, fontSize: 12.5, color: "var(--fg-subtle)" }}>
            {agent.provider && (
              <div>
                {t("agentDetail.providerLabel")}<b style={{ color: "var(--fg-muted)" }}>{agent.provider}</b>
              </div>
            )}
            <div>
              {t("agentDetail.createdAtLabel")}<b style={{ color: "var(--fg-muted)" }}>{formatDate(agent.created_at)}</b>
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
                icon_path: agent.icon_path ?? undefined,
                category: agent.category,
                hello_msg: agent.hello_msg ?? undefined,
                example_questions: agent.example_questions,
              });
              setEditOpen(true);
            }}
          >
            {t("common.edit")}
          </Button>
          <Popconfirm
            title={t("agentDetail.deleteConfirmTitle")}
            description={t("agentDetail.deleteConfirmDesc")}
            onConfirm={() => deleteMutation.mutate()}
            okText={t("common.delete")}
            okButtonProps={{ danger: true }}
            cancelText={t("common.cancel")}
          >
            <Button danger loading={deleteMutation.isPending}>
              {t("common.delete")}
            </Button>
          </Popconfirm>
          <Button onClick={() => setInviteOpen(true)}>{t("agentDetail.inviteMember")}</Button>
          <Button
            type="primary"
            loading={createVersionMutation.isPending}
            onClick={() => createVersionMutation.mutate()}
          >
            {t("agentDetail.addVersion")}
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
        locale={{ emptyText: t("agentDetail.versionsEmpty") }}
        columns={[
          { title: t("common.version"), dataIndex: "version", render: (v: number) => `v${v}` },
          { title: t("common.status"), dataIndex: "status", render: (s: AgentVersion["status"]) => <VersionStatusTag status={s} /> },
          { title: t("agentDetail.streamingCol"), dataIndex: "streaming", render: (v: boolean) => (v ? t("common.yes") : t("common.no")) },
          {
            title: t("common.updatedAt"),
            dataIndex: "updated_at",
            render: (v: string) => formatDateTime(v),
          },
        ]}
      />

      <Typography.Title level={5} style={{ marginBottom: 12 }}>
        {t("agentDetail.membersTitle")}
      </Typography.Title>
      {membersQuery.data && membersQuery.data.length > 0 ? (
        <div style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", borderRadius: 8 }}>
          {membersQuery.data.map((m, idx) => (
            <div
              key={m.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "13px 18px",
                borderBottom: idx === membersQuery.data.length - 1 ? "none" : "1px solid var(--border-default)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Avatar size={22} style={{ background: "var(--color-brand-tint)", color: "var(--fg-on-brand-tint)", fontSize: 10 }}>
                  {m.user_id.slice(0, 1).toUpperCase()}
                </Avatar>
                <span style={{ fontSize: 12.5, fontFamily: "monospace", color: "var(--fg-muted)" }}>{m.user_id}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <AssetRoleTag role={m.role} />
                {m.role !== "owner" && (
                  <Popconfirm
                    title={t("agentDetail.removeMemberConfirmTitle")}
                    onConfirm={() => removeMutation.mutate(m.user_id)}
                    okText={t("common.remove")}
                    cancelText={t("common.cancel")}
                  >
                    <Button size="small" type="text" danger>
                      {t("common.remove")}
                    </Button>
                  </Popconfirm>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Empty description={t("agentDetail.membersEmpty")} />
      )}

      <Modal
        title={t("agentDetail.editModalTitle")}
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={() => editForm.submit()}
        confirmLoading={updateMutation.isPending}
        okText={t("common.save")}
        cancelText={t("common.cancel")}
      >
        <Form form={editForm} layout="vertical" onFinish={(v) => updateMutation.mutate(v)}>
          <Form.Item label={t("common.name")} name="name" rules={[{ required: true, message: t("common.nameRequired") }]}>
            <Input />
          </Form.Item>
          <Form.Item label={t("common.description")} name="description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item label="Provider" name="provider">
            <Input />
          </Form.Item>
          <Form.Item label="Visibility" name="visibility" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "private", label: t("common.visibilityOptions.private") },
                { value: "internal", label: t("common.visibilityOptions.internal") },
                { value: "public", label: t("common.visibilityOptions.public") },
              ]}
            />
          </Form.Item>
          <AgentFormFields />
        </Form>
      </Modal>

      <Modal
        title={t("agentDetail.inviteModalTitle")}
        open={inviteOpen}
        onCancel={() => setInviteOpen(false)}
        onOk={() => inviteForm.submit()}
        confirmLoading={inviteMutation.isPending}
        okText={t("agentDetail.inviteOk")}
        cancelText={t("common.cancel")}
      >
        <Form form={inviteForm} layout="vertical" onFinish={(v) => inviteMutation.mutate(v.user_id)}>
          <Form.Item
            label="User ID"
            name="user_id"
            rules={[{ required: true, message: t("agentDetail.userIdRequired") }]}
            extra={t("agentDetail.inviteExtra")}
          >
            <Input placeholder="00000000-0000-0000-0000-000000000000" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
