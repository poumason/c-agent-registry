import { DownloadOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App,
  Breadcrumb,
  Button,
  Empty,
  Form,
  Grid,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Spin,
  Switch,
  Tag,
  Typography,
} from "antd";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { listSkills, listMcps } from "../api/skills";
import { listReviewerCandidates, listVersionReviews } from "../api/reviews";
import type { DependencyType } from "../api/types";
import {
  activateVersion,
  addDependency,
  deactivateVersion,
  getDownloadUrl,
  getVersion,
  listDependencies,
  removeDependency,
  submitVersion,
  updateVersion,
} from "../api/versions";
import { ReviewResultTag, VersionStatusTag } from "../components/tags";

export default function VersionDetail() {
  const { message } = App.useApp();
  const screens = Grid.useBreakpoint();
  const { agentSlug, versionSlug } = useParams<{ agentSlug: string; versionSlug: string }>();
  const queryClient = useQueryClient();
  const [submitOpen, setSubmitOpen] = useState(false);
  const [depOpen, setDepOpen] = useState(false);
  const [submitForm] = Form.useForm<{ reviewer_ids: string[] }>();
  const [depForm] = Form.useForm<{ type: DependencyType; dependency_id: string }>();

  const versionQuery = useQuery({
    queryKey: ["version", versionSlug],
    queryFn: () => getVersion(versionSlug!),
    enabled: !!versionSlug,
  });
  const depsQuery = useQuery({
    queryKey: ["version-deps", versionSlug],
    queryFn: () => listDependencies(versionSlug!),
    enabled: !!versionSlug,
  });
  const reviewsQuery = useQuery({
    queryKey: ["version-reviews", versionSlug],
    queryFn: () => listVersionReviews(versionSlug!),
    enabled: !!versionSlug,
  });
  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: listSkills });
  const mcpsQuery = useQuery({ queryKey: ["mcps"], queryFn: listMcps });
  const reviewerCandidatesQuery = useQuery({
    queryKey: ["reviewer-candidates"],
    queryFn: listReviewerCandidates,
  });

  const skillNameById = useMemo(
    () => new Map((skillsQuery.data ?? []).map((s) => [s.id, `${s.name} v${s.version}`])),
    [skillsQuery.data],
  );
  const mcpNameById = useMemo(
    () => new Map((mcpsQuery.data ?? []).map((m) => [m.id, `${m.name} v${m.version}`])),
    [mcpsQuery.data],
  );

  const invalidateVersion = () => {
    queryClient.invalidateQueries({ queryKey: ["version", versionSlug] });
    queryClient.invalidateQueries({ queryKey: ["agent-versions", agentSlug] });
  };

  const submitMutation = useMutation({
    mutationFn: (reviewerIds: string[]) => submitVersion(versionSlug!, reviewerIds),
    onSuccess: () => {
      message.success("已送審");
      invalidateVersion();
      queryClient.invalidateQueries({ queryKey: ["version-reviews", versionSlug] });
      setSubmitOpen(false);
      submitForm.resetFields();
    },
    onError: () => message.error("送審失敗，請確認選擇的審核者有效"),
  });

  const activateMutation = useMutation({
    mutationFn: () => activateVersion(versionSlug!),
    onSuccess: () => {
      message.success("已啟用");
      invalidateVersion();
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(msg ?? "啟用失敗");
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateVersion(versionSlug!),
    onSuccess: () => {
      message.success("已停用");
      invalidateVersion();
    },
    onError: () => message.error("停用失敗"),
  });

  const downloadMutation = useMutation({
    mutationFn: () => getDownloadUrl(versionSlug!),
    onSuccess: (url) => window.open(url, "_blank"),
    onError: () => message.error("下載連結取得失敗，這個版本可能還沒通過審核"),
  });

  const addDepMutation = useMutation({
    mutationFn: (values: { type: DependencyType; dependency_id: string }) =>
      addDependency(versionSlug!, values.dependency_id, values.type),
    onSuccess: () => {
      message.success("已加入依賴");
      queryClient.invalidateQueries({ queryKey: ["version-deps", versionSlug] });
      setDepOpen(false);
      depForm.resetFields();
    },
    onError: () => message.error("加入失敗"),
  });

  const removeDepMutation = useMutation({
    mutationFn: (rowId: string) => removeDependency(versionSlug!, rowId),
    onSuccess: () => {
      message.success("已移除依賴");
      queryClient.invalidateQueries({ queryKey: ["version-deps", versionSlug] });
    },
    onError: () => message.error("移除失敗"),
  });

  const saveParamsMutation = useMutation({
    mutationFn: (values: { url?: string; streaming?: boolean }) =>
      updateVersion(versionSlug!, values),
    onSuccess: () => {
      message.success("已儲存");
      invalidateVersion();
    },
    onError: () => message.error("儲存失敗"),
  });

  if (versionQuery.isLoading || !versionQuery.data) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }
  const version = versionQuery.data;
  const isRejected = version.status === "rejected";
  // Rejected versions are fixed in place and resubmitted rather than forking a new
  // version, so review history keeps accumulating on this same version slug.
  const isEditable = version.status === "draft" || isRejected;

  return (
    <div>
      <Breadcrumb
        items={[
          { title: <Link to="/my-agents">Agents</Link> },
          { title: <Link to={`/agents/${agentSlug}`}>{agentSlug}</Link> },
          { title: `v${version.version}` },
        ]}
        style={{ marginBottom: 8, fontSize: 12.5 }}
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginBottom: 22 }}>
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4, display: "flex", alignItems: "center", gap: 10 }}>
            {version.slug}
            <VersionStatusTag status={version.status} />
          </Typography.Title>
          <div style={{ fontSize: 12.5, color: "#9AA0AC" }}>
            最後更新：{new Date(version.updated_at).toLocaleString()}
          </div>
        </div>
        <Space>
          {isEditable && (
            <Button type="primary" onClick={() => setSubmitOpen(true)}>
              {isRejected ? "重新送審" : "送審"}
            </Button>
          )}
          {version.status === "approved" && (
            <Button onClick={() => activateMutation.mutate()} loading={activateMutation.isPending}>
              啟用
            </Button>
          )}
          {version.status === "active" && (
            <Popconfirm title="確定要停用這個版本嗎？" onConfirm={() => deactivateMutation.mutate()} okText="停用" cancelText="取消">
              <Button danger>停用</Button>
            </Popconfirm>
          )}
          {version.package_path && (
            <Button icon={<DownloadOutlined />} onClick={() => downloadMutation.mutate()} loading={downloadMutation.isPending}>
              下載安裝包
            </Button>
          )}
        </Space>
      </div>

      {version.status === "draft" && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 18 }}
          title="草稿可以自由編輯"
          description="下面的參數與依賴會在你按「儲存」/「加入」時個別存檔，草稿狀態下可以反覆修改、不影響任何人。按下右上角「送審」並選好審核者、確認送出後，才會正式進入審核，且版本會被鎖定、無法再編輯。"
        />
      )}
      {version.status === "in_review" && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 18 }}
          title="審核中，已鎖定編輯"
          description="這個版本已送審，等待右側審核者做出決定前無法修改參數或依賴。"
        />
      )}
      {isRejected && (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 18 }}
          title="已被退回，可以直接修改後重新送審"
          description="請參考右側審核紀錄裡的意見，改好下面的參數或依賴後按右上角「重新送審」，不用另外建立新版本——這個版本的審核紀錄會持續累積，之前的退回意見也會留著。"
        />
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: screens.lg ? "1.5fr 1fr" : "1fr",
          gap: 20,
          alignItems: "start",
        }}
      >
        <div>
          <div style={{ background: "#fff", border: "1px solid #E4E6EC", borderRadius: 8, padding: 20, marginBottom: 18 }}>
            <Typography.Title level={5} style={{ marginBottom: 14 }}>
              執行參數
            </Typography.Title>
            <Form
              layout="vertical"
              initialValues={{ url: version.url ?? "", streaming: version.streaming }}
              onFinish={(v) => saveParamsMutation.mutate(v)}
              disabled={!isEditable}
            >
              <Form.Item label="Endpoint URL" name="url">
                <Input placeholder="https://agents.example.com/your-agent" />
              </Form.Item>
              <Form.Item label="Streaming" name="streaming" valuePropName="checked">
                <Switch />
              </Form.Item>
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: "#9AA0AC", marginBottom: 6 }}>
                  DEFAULT INPUT MODES
                </div>
                <Space wrap>
                  {version.default_input_modes.length
                    ? version.default_input_modes.map((m) => <Tag key={m}>{m}</Tag>)
                    : <Typography.Text type="secondary">（無）</Typography.Text>}
                </Space>
              </div>
              <div style={{ marginBottom: isEditable ? 14 : 0 }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: "#9AA0AC", marginBottom: 6 }}>
                  DEFAULT OUTPUT MODES
                </div>
                <Space wrap>
                  {version.default_output_modes.length
                    ? version.default_output_modes.map((m) => <Tag key={m}>{m}</Tag>)
                    : <Typography.Text type="secondary">（無）</Typography.Text>}
                </Space>
              </div>
              {isEditable && (
                <Button htmlType="submit" loading={saveParamsMutation.isPending}>
                  儲存參數
                </Button>
              )}
            </Form>
          </div>

          <div style={{ background: "#fff", border: "1px solid #E4E6EC", borderRadius: 8, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <Typography.Title level={5} style={{ marginBottom: 0 }}>
                依賴的 Skill / MCP
              </Typography.Title>
              {isEditable && (
                <Button size="small" onClick={() => setDepOpen(true)}>
                  新增依賴
                </Button>
              )}
            </div>
            {depsQuery.data && depsQuery.data.length > 0 ? (
              <Space wrap>
                {depsQuery.data.map((d) => {
                  const label =
                    d.type === "skill"
                      ? skillNameById.get(d.dependency_id) ?? d.dependency_id
                      : mcpNameById.get(d.dependency_id) ?? d.dependency_id;
                  return (
                    <Tag
                      key={d.id}
                      color={d.type === "mcp" ? "geekblue" : "default"}
                      closable={isEditable}
                      onClose={(e) => {
                        e.preventDefault();
                        removeDepMutation.mutate(d.id);
                      }}
                    >
                      {label} <span style={{ opacity: 0.6 }}>{d.type}</span>
                    </Tag>
                  );
                })}
              </Space>
            ) : (
              <Typography.Text type="secondary">尚未加入任何依賴</Typography.Text>
            )}
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid #E4E6EC", borderRadius: 8, padding: 20 }}>
          <Typography.Title level={5} style={{ marginBottom: 14 }}>
            審核紀錄
          </Typography.Title>
          {reviewsQuery.data && reviewsQuery.data.length > 0 ? (
            <Space orientation="vertical" style={{ width: "100%" }} size={14}>
              {reviewsQuery.data.map((r) => (
                <div key={r.id}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontSize: 12.5, fontFamily: "monospace", color: "#6B7280" }}>
                      {r.reviewer_id.slice(0, 8)}…
                    </div>
                    <ReviewResultTag result={r.result} />
                  </div>
                  {r.comment && (
                    <Typography.Paragraph
                      type="secondary"
                      style={{ fontSize: 12.5, whiteSpace: "pre-wrap", marginTop: 4, marginBottom: 0 }}
                    >
                      {r.comment}
                    </Typography.Paragraph>
                  )}
                </div>
              ))}
            </Space>
          ) : (
            <Empty description="尚未送審" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </div>
      </div>

      <Modal
        title="送審"
        open={submitOpen}
        onCancel={() => setSubmitOpen(false)}
        onOk={() => submitForm.submit()}
        confirmLoading={submitMutation.isPending}
        okText="送出"
        cancelText="取消"
      >
        <Form
          form={submitForm}
          layout="vertical"
          onFinish={(v) => submitMutation.mutate(v.reviewer_ids ?? [])}
        >
          <Form.Item
            label="指定審核者（選填）"
            name="reviewer_ids"
            extra="只能指定系統角色為 reviewer 或 admin 的使用者。不選就自動通知所有 reviewer/admin。"
          >
            <Select
              mode="multiple"
              placeholder="不選就自動通知所有審核者"
              loading={reviewerCandidatesQuery.isLoading}
              options={(reviewerCandidatesQuery.data ?? []).map((c) => ({
                value: c.id,
                label: `${c.name} (${c.email})`,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新增依賴"
        open={depOpen}
        onCancel={() => setDepOpen(false)}
        onOk={() => depForm.submit()}
        confirmLoading={addDepMutation.isPending}
        okText="加入"
        cancelText="取消"
      >
        <Form
          form={depForm}
          layout="vertical"
          initialValues={{ type: "skill" }}
          onFinish={(v) => addDepMutation.mutate(v)}
        >
          <Form.Item label="類型" name="type" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "skill", label: "Skill" },
                { value: "mcp", label: "MCP" },
              ]}
            />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.type !== cur.type}>
            {({ getFieldValue }) => {
              const type: DependencyType = getFieldValue("type");
              const options =
                type === "skill"
                  ? (skillsQuery.data ?? []).map((s) => ({ value: s.id, label: `${s.name} v${s.version}` }))
                  : (mcpsQuery.data ?? []).map((m) => ({ value: m.id, label: `${m.name} v${m.version}` }));
              return (
                <Form.Item label={type === "skill" ? "Skill" : "MCP"} name="dependency_id" rules={[{ required: true }]}>
                  <Select options={options} placeholder="選擇" showSearch optionFilterProp="label" />
                </Form.Item>
              );
            }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
