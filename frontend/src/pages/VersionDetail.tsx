import { DownloadOutlined, MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App,
  Breadcrumb,
  Button,
  Checkbox,
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
  Tabs,
  Tag,
  Typography,
} from "antd";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { listFabs, listSkills, listMcps } from "../api/skills";
import { getRegistryOverview } from "../api/registry";
import { decideReview, listReviewerCandidates, listVersionReviews } from "../api/reviews";
import type { AgentCardSkillEntry, DependencySource, DependencyType } from "../api/types";
import type { AgentDependency } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import {
  activateVersion,
  addDependency,
  deactivateVersion,
  getAgentCard,
  getDownloadUrl,
  getVersion,
  listDependencies,
  listVersionFabs,
  removeDependency,
  setVersionFabs,
  submitVersion,
  updateVersion,
} from "../api/versions";
import { ReviewResultTag, VersionStatusTag } from "../components/tags";
import { useFormatters } from "../lib/relativeTime";

export default function VersionDetail() {
  const { t } = useTranslation();
  const { formatDateTime } = useFormatters();
  const { message } = App.useApp();
  const { user } = useAuth();
  const screens = Grid.useBreakpoint();
  const { agentSlug, versionSlug } = useParams<{ agentSlug: string; versionSlug: string }>();
  const queryClient = useQueryClient();
  const [submitOpen, setSubmitOpen] = useState(false);
  const [depOpen, setDepOpen] = useState(false);
  // Which fab tab's "Add Dependency" button opened the modal — null when opened
  // from the no-fabs-deployed empty state (fab_id stays unset in that case too).
  const [depTargetFabId, setDepTargetFabId] = useState<string | null>(null);
  const [manageFabsOpen, setManageFabsOpen] = useState(false);
  const [submitForm] = Form.useForm<{ reviewer_ids: string[] }>();
  const [depForm] = Form.useForm<{ type: DependencyType; dependency_id: string }>();
  const [skillsForm] = Form.useForm<{ skills: AgentCardSkillEntry[] }>();
  const [decisionComments, setDecisionComments] = useState<Record<string, string>>({});
  // checked[fab_id] -> url input value. Seeded from the saved agent_fabs once loaded
  // (see the useEffect below), then edited freely until "Save" is pressed.
  const [fabUrls, setFabUrls] = useState<Record<string, string>>({});

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
  // Skill's registry-sourced options — see UI_AUDIT.md's registry-migration note.
  // Currently always empty until the real sync integration lands
  // (app/crud/registry.py), so this query just contributes nothing to the picker
  // below yet, not an error. MCP has no equivalent — it resolves against the real
  // mcps table (with its own available/unavailable sync) instead, see the dependency
  // picker below.
  const skillhubRegistryQuery = useQuery({
    queryKey: ["admin-registry", "skillhub-registry"],
    queryFn: () => getRegistryOverview("skillhub-registry"),
  });
  const reviewerCandidatesQuery = useQuery({
    queryKey: ["reviewer-candidates"],
    queryFn: listReviewerCandidates,
  });
  const fabsQuery = useQuery({ queryKey: ["fabs"], queryFn: listFabs });
  const versionFabsQuery = useQuery({
    queryKey: ["version-fabs", versionSlug],
    queryFn: () => listVersionFabs(versionSlug!),
    enabled: !!versionSlug,
  });
  const agentCardQuery = useQuery({
    queryKey: ["agent-card", versionSlug],
    queryFn: () => getAgentCard(versionSlug!),
    enabled: !!versionSlug,
  });

  // Re-seed the checkbox/url editing state whenever the saved assignment changes
  // (initial load, or after a successful save re-fetches it).
  useEffect(() => {
    if (versionFabsQuery.data) {
      setFabUrls(Object.fromEntries(versionFabsQuery.data.map((f) => [f.fab_id, f.url ?? ""])));
    }
  }, [versionFabsQuery.data]);

  useEffect(() => {
    if (versionQuery.data) {
      skillsForm.setFieldsValue({ skills: versionQuery.data.skills });
    }
  }, [versionQuery.data, skillsForm]);

  const skillNameById = useMemo(
    () => new Map((skillsQuery.data ?? []).map((s) => [s.id, `${s.name} v${s.version}`])),
    [skillsQuery.data],
  );
  const mcpNameById = useMemo(
    () => new Map((mcpsQuery.data ?? []).map((m) => [m.id, `${m.name} v${m.version}`])),
    [mcpsQuery.data],
  );
  const skillhubItemNameById = useMemo(
    () => new Map((skillhubRegistryQuery.data?.items ?? []).map((i) => [i.id, i.name])),
    [skillhubRegistryQuery.data],
  );
  const fabNameById = useMemo(
    () => new Map((fabsQuery.data ?? []).map((f) => [f.id, f.fab])),
    [fabsQuery.data],
  );

  // A fab's effective dependency set: rows scoped to it, plus fab-agnostic ones
  // (fab_id === null — model/registry dependencies, see app/services/fab_scope.py).
  const depsForFab = (fabId: string) =>
    (depsQuery.data ?? []).filter((d) => d.fab_id === fabId || d.fab_id === null);

  // What the agent card looks like reached at this one fab — same shared identity/
  // capabilities/skills as agentCardQuery.data, just this fab's single interface
  // instead of the full aggregate list. Computed client-side; GET .../agent-card
  // itself stays version-wide (see app/services/agent_card.py).
  const cardForFab = (fabId: string) => {
    if (!agentCardQuery.data) return undefined;
    const url = fabUrls[fabId];
    return {
      ...agentCardQuery.data,
      supportedInterfaces: url ? [{ url, protocolBinding: "JSONRPC", protocolVersion: "1.0" }] : [],
    };
  };

  const renderDependencyTag = (d: AgentDependency) => {
    // "registry" source only ever applies to skill dependencies now (see the
    // picker below) — an mcp/registry row could only exist from before this
    // reconciliation, and falls back to the dependency_id itself.
    const legacyName = d.type === "skill" ? skillNameById.get(d.dependency_id) : mcpNameById.get(d.dependency_id);
    const registryName = d.type === "skill" ? skillhubItemNameById.get(d.dependency_id) : undefined;
    const label = (d.source === "registry" ? registryName : legacyName) ?? d.dependency_id;
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
        {label}{" "}
        <span style={{ opacity: 0.6 }}>
          {d.type}
          {d.source === "registry" ? " · synced" : ""}
          {d.fab_id === null ? ` · ${t("versionDetail.sharedDependencyBadge")}` : ""}
        </span>
      </Tag>
    );
  };

  // Pending reviews the current user can act on right now — mirrors decide_review's
  // own permission check (assigned reviewer, or admin overriding anyone's). Once the
  // version leaves in_review (someone already decided), nothing is actionable even if
  // a row is still technically "pending" (the other assigned reviewers never got to).
  const actionableReviews = useMemo(() => {
    if (!user || versionQuery.data?.status !== "in_review") return [];
    return (reviewsQuery.data ?? []).filter(
      (r) => r.result === "pending" && (r.reviewer_id === user.id || user.role === "admin"),
    );
  }, [reviewsQuery.data, versionQuery.data?.status, user]);
  const invalidateVersion = () => {
    queryClient.invalidateQueries({ queryKey: ["version", versionSlug] });
    queryClient.invalidateQueries({ queryKey: ["agent-versions", agentSlug] });
  };

  const submitMutation = useMutation({
    mutationFn: (reviewerIds: string[]) => submitVersion(versionSlug!, reviewerIds),
    onSuccess: () => {
      message.success(t("versionDetail.submitSuccess"));
      invalidateVersion();
      queryClient.invalidateQueries({ queryKey: ["version-reviews", versionSlug] });
      setSubmitOpen(false);
      submitForm.resetFields();
    },
    onError: () => message.error(t("versionDetail.submitFailed")),
  });

  const decisionMutation = useMutation({
    mutationFn: ({ reviewId, result }: { reviewId: string; result: "approved" | "rejected" }) =>
      decideReview(reviewId, result, decisionComments[reviewId]?.trim() || undefined),
    onSuccess: () => {
      message.success(t("versionDetail.decisionSuccess"));
      invalidateVersion();
      queryClient.invalidateQueries({ queryKey: ["version-reviews", versionSlug] });
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(msg ?? t("versionDetail.decisionFailed"));
    },
  });

  const activateMutation = useMutation({
    mutationFn: () => activateVersion(versionSlug!),
    onSuccess: () => {
      message.success(t("versionDetail.activateSuccess"));
      invalidateVersion();
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(msg ?? t("versionDetail.activateFailed"));
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateVersion(versionSlug!),
    onSuccess: () => {
      message.success(t("versionDetail.deactivateSuccess"));
      invalidateVersion();
    },
    onError: () => message.error(t("versionDetail.deactivateFailed")),
  });

  const downloadMutation = useMutation({
    mutationFn: () => getDownloadUrl(versionSlug!),
    onSuccess: (url) => window.open(url, "_blank"),
    onError: () => message.error(t("versionDetail.downloadLinkFailed")),
  });

  const addDepMutation = useMutation({
    mutationFn: (values: {
      type: DependencyType;
      dependency_id: string;
      source: DependencySource;
      fab_id: string | null;
    }) => addDependency(versionSlug!, values.dependency_id, values.type, values.source, values.fab_id),
    onSuccess: () => {
      message.success(t("versionDetail.addDependencySuccess"));
      queryClient.invalidateQueries({ queryKey: ["version-deps", versionSlug] });
      setDepOpen(false);
      depForm.resetFields();
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(msg ?? t("versionDetail.addDependencyFailed"));
    },
  });

  const removeDepMutation = useMutation({
    mutationFn: (rowId: string) => removeDependency(versionSlug!, rowId),
    onSuccess: () => {
      message.success(t("versionDetail.removeDependencySuccess"));
      queryClient.invalidateQueries({ queryKey: ["version-deps", versionSlug] });
    },
    onError: () => message.error(t("common.removeFailed")),
  });

  const saveParamsMutation = useMutation({
    mutationFn: (values: { streaming?: boolean }) => updateVersion(versionSlug!, values),
    onSuccess: () => {
      message.success(t("versionDetail.saveSuccess"));
      invalidateVersion();
    },
    onError: () => message.error(t("versionDetail.saveFailed")),
  });

  const saveFabsMutation = useMutation({
    mutationFn: () =>
      setVersionFabs(
        versionSlug!,
        Object.entries(fabUrls).map(([fab_id, url]) => ({ fab_id, url })),
      ),
    onSuccess: () => {
      message.success(t("versionDetail.fabsSaveSuccess"));
      queryClient.invalidateQueries({ queryKey: ["version-fabs", versionSlug] });
      queryClient.invalidateQueries({ queryKey: ["agent-card", versionSlug] });
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(msg ?? t("versionDetail.fabsSaveFailed"));
    },
  });

  const saveSkillsMutation = useMutation({
    mutationFn: (skills: AgentCardSkillEntry[]) => updateVersion(versionSlug!, { skills }),
    onSuccess: () => {
      message.success(t("versionDetail.skillsSaveSuccess"));
      invalidateVersion();
      queryClient.invalidateQueries({ queryKey: ["agent-card", versionSlug] });
    },
    onError: () => message.error(t("versionDetail.skillsSaveFailed")),
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
          <div style={{ fontSize: 12.5, color: "var(--fg-subtle)" }}>
            {t("versionDetail.lastUpdated", { date: formatDateTime(version.updated_at) })}
          </div>
        </div>
        <Space>
          {isEditable && (
            <Button type="primary" onClick={() => setSubmitOpen(true)}>
              {isRejected ? t("versionDetail.resubmit") : t("common.submit")}
            </Button>
          )}
          {version.status === "approved" && (
            <Button onClick={() => activateMutation.mutate()} loading={activateMutation.isPending}>
              {t("versionDetail.activate")}
            </Button>
          )}
          {version.status === "active" && (
            <Popconfirm
              title={t("versionDetail.deactivateConfirm")}
              onConfirm={() => deactivateMutation.mutate()}
              okText={t("versionDetail.deactivate")}
              cancelText={t("common.cancel")}
            >
              <Button danger>{t("versionDetail.deactivate")}</Button>
            </Popconfirm>
          )}
          {version.package_path && (
            <Button icon={<DownloadOutlined />} onClick={() => downloadMutation.mutate()} loading={downloadMutation.isPending}>
              {t("versionDetail.downloadPackage")}
            </Button>
          )}
        </Space>
      </div>

      {version.status === "draft" && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 18 }}
          title={t("versionDetail.draftAlertTitle")}
          description={t("versionDetail.draftAlertDesc")}
        />
      )}
      {version.status === "in_review" && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 18 }}
          title={t("versionDetail.inReviewAlertTitle")}
          description={t("versionDetail.inReviewAlertDesc")}
        />
      )}
      {isRejected && (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 18 }}
          title={t("versionDetail.rejectedAlertTitle")}
          description={t("versionDetail.rejectedAlertDesc")}
        />
      )}

      {actionableReviews.length > 0 && (
        <div
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--color-brand)",
            borderRadius: 8,
            padding: 20,
            marginBottom: 18,
          }}
        >
          <Typography.Title level={5} style={{ marginBottom: 6 }}>
            {t("versionDetail.pendingDecisionTitle")}
          </Typography.Title>
          <Typography.Text type="secondary" style={{ fontSize: 12.5, display: "block", marginBottom: 14 }}>
            {t("versionDetail.pendingDecisionDesc")}
          </Typography.Text>
          <Space orientation="vertical" style={{ width: "100%" }} size={16}>
            {actionableReviews.map((r, idx) => {
              const comment = decisionComments[r.id] ?? "";
              const isMine = r.reviewer_id === user?.id;
              return (
                <div
                  key={r.id}
                  style={idx > 0 ? { borderTop: "1px solid var(--border-default)", paddingTop: 14 } : undefined}
                >
                  {!isMine && (
                    <div style={{ fontSize: 12, color: "var(--fg-subtle)", marginBottom: 6 }}>
                      {t("versionDetail.decidingAsAdminFor", { reviewer: r.reviewer_id.slice(0, 8) })}
                    </div>
                  )}
                  <Input.TextArea
                    rows={3}
                    placeholder={t("versionDetail.decisionCommentPlaceholder")}
                    value={comment}
                    onChange={(e) => setDecisionComments((prev) => ({ ...prev, [r.id]: e.target.value }))}
                    style={{ marginBottom: 10 }}
                  />
                  <Space>
                    <Button
                      type="primary"
                      loading={decisionMutation.isPending}
                      onClick={() => decisionMutation.mutate({ reviewId: r.id, result: "approved" })}
                    >
                      {t("versionDetail.approve")}
                    </Button>
                    <Button
                      danger
                      loading={decisionMutation.isPending}
                      disabled={!comment.trim()}
                      onClick={() => decisionMutation.mutate({ reviewId: r.id, result: "rejected" })}
                    >
                      {t("versionDetail.reject")}
                    </Button>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {t("versionDetail.rejectRequiresComment")}
                    </Typography.Text>
                  </Space>
                </div>
              );
            })}
          </Space>
        </div>
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
          <div style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", borderRadius: 8, padding: 20, marginBottom: 18 }}>
            <Typography.Title level={5} style={{ marginBottom: 14 }}>
              {t("versionDetail.paramsTitle")}
            </Typography.Title>
            <Form
              layout="vertical"
              initialValues={{ streaming: version.streaming }}
              onFinish={(v) => saveParamsMutation.mutate(v)}
              disabled={!isEditable}
            >
              <Form.Item label="Streaming" name="streaming" valuePropName="checked">
                <Switch />
              </Form.Item>
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)", marginBottom: 6 }}>
                  DEFAULT INPUT MODES
                </div>
                <Space wrap>
                  {version.default_input_modes.length
                    ? version.default_input_modes.map((m) => <Tag key={m}>{m}</Tag>)
                    : <Typography.Text type="secondary">{t("common.none")}</Typography.Text>}
                </Space>
              </div>
              <div style={{ marginBottom: isEditable ? 14 : 0 }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)", marginBottom: 6 }}>
                  DEFAULT OUTPUT MODES
                </div>
                <Space wrap>
                  {version.default_output_modes.length
                    ? version.default_output_modes.map((m) => <Tag key={m}>{m}</Tag>)
                    : <Typography.Text type="secondary">{t("common.none")}</Typography.Text>}
                </Space>
              </div>
              {isEditable && (
                <Button htmlType="submit" loading={saveParamsMutation.isPending}>
                  {t("versionDetail.saveParams")}
                </Button>
              )}
            </Form>
          </div>

          <div style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", borderRadius: 8, padding: 20, marginBottom: 18 }}>
            <Typography.Title level={5} style={{ marginBottom: 6 }}>
              {t("versionDetail.skillsEditorTitle")}
            </Typography.Title>
            <Typography.Text type="secondary" style={{ fontSize: 12.5, display: "block", marginBottom: 14 }}>
              {t("versionDetail.skillsEditorDesc")}
            </Typography.Text>
            <Form
              form={skillsForm}
              layout="vertical"
              disabled={!isEditable}
              onFinish={(v: { skills?: AgentCardSkillEntry[] }) => saveSkillsMutation.mutate(v.skills ?? [])}
            >
              <Form.List name="skills">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map(({ key, name, ...rest }) => (
                      <div
                        key={key}
                        style={{ border: "1px solid var(--border-default)", borderRadius: 8, padding: 14, marginBottom: 12 }}
                      >
                        <div style={{ display: "flex", justifyContent: "flex-end" }}>
                          <Button type="text" danger size="small" icon={<MinusCircleOutlined />} onClick={() => remove(name)}>
                            {t("common.remove")}
                          </Button>
                        </div>
                        <Form.Item {...rest} label="ID" name={[name, "id"]} rules={[{ required: true }]}>
                          <Input placeholder="route-optimizer-traffic" />
                        </Form.Item>
                        <Form.Item {...rest} label={t("common.name")} name={[name, "name"]} rules={[{ required: true }]}>
                          <Input placeholder="Traffic-Aware Route Optimizer" />
                        </Form.Item>
                        <Form.Item {...rest} label={t("common.description")} name={[name, "description"]}>
                          <Input.TextArea rows={2} />
                        </Form.Item>
                        <Form.Item {...rest} label={t("versionDetail.skillTagsLabel")} name={[name, "tags"]}>
                          <Select mode="tags" tokenSeparators={[","]} open={false} />
                        </Form.Item>
                        <Form.Item {...rest} label={t("versionDetail.skillExamplesLabel")} name={[name, "examples"]}>
                          <Select mode="tags" tokenSeparators={["\n"]} open={false} placeholder={t("versionDetail.examplesPlaceholder")} />
                        </Form.Item>
                        <Form.Item {...rest} label={t("versionDetail.skillInputModesLabel")} name={[name, "inputModes"]}>
                          <Select mode="tags" tokenSeparators={[","]} open={false} placeholder="application/json" />
                        </Form.Item>
                        <Form.Item {...rest} label={t("versionDetail.skillOutputModesLabel")} name={[name, "outputModes"]}>
                          <Select mode="tags" tokenSeparators={[","]} open={false} placeholder="application/json" />
                        </Form.Item>
                      </div>
                    ))}
                    {isEditable && (
                      <Button
                        type="dashed"
                        block
                        icon={<PlusOutlined />}
                        onClick={() =>
                          add({ id: "", name: "", description: "", tags: [], examples: [], inputModes: [], outputModes: [] })
                        }
                      >
                        {t("versionDetail.addSkillCard")}
                      </Button>
                    )}
                  </>
                )}
              </Form.List>
              {isEditable && (
                <Button htmlType="submit" type="primary" style={{ marginTop: 14 }} loading={saveSkillsMutation.isPending}>
                  {t("versionDetail.skillsSave")}
                </Button>
              )}
            </Form>
          </div>

          <div style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", borderRadius: 8, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <Typography.Title level={5} style={{ marginBottom: 0 }}>
                {t("versionDetail.fabsTitle")}
              </Typography.Title>
              {isEditable && (
                <Button size="small" onClick={() => setManageFabsOpen(true)}>
                  {t("versionDetail.manageFabs")}
                </Button>
              )}
            </div>
            <Typography.Text type="secondary" style={{ fontSize: 12.5, display: "block", marginBottom: 14 }}>
              {t("versionDetail.fabsDesc")}
            </Typography.Text>

            {(versionFabsQuery.data ?? []).length > 0 ? (
              <Tabs
                items={(versionFabsQuery.data ?? []).map((vf) => {
                  const fabId = vf.fab_id;
                  const fabName = fabNameById.get(fabId) ?? fabId;
                  const deps = depsForFab(fabId);
                  const card = cardForFab(fabId);
                  return {
                    key: fabId,
                    label: fabName,
                    children: (
                      <div>
                        <div style={{ marginBottom: 18 }}>
                          <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)", marginBottom: 6 }}>
                            {t("versionDetail.fabUrlLabel")}
                          </div>
                          <Space.Compact style={{ width: "100%" }}>
                            <Input
                              placeholder="https://agents.example.com/your-agent"
                              value={fabUrls[fabId] ?? ""}
                              disabled={!isEditable}
                              onChange={(e) => setFabUrls((prev) => ({ ...prev, [fabId]: e.target.value }))}
                            />
                            {isEditable && (
                              <Button
                                onClick={() => saveFabsMutation.mutate()}
                                loading={saveFabsMutation.isPending}
                                disabled={!(fabUrls[fabId] ?? "").trim()}
                              >
                                {t("versionDetail.saveFabUrl")}
                              </Button>
                            )}
                          </Space.Compact>
                        </div>

                        <div style={{ marginBottom: 18 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                            <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)" }}>
                              {t("versionDetail.dependenciesTitle")}
                            </div>
                            {isEditable && (
                              <Button
                                size="small"
                                onClick={() => {
                                  setDepTargetFabId(fabId);
                                  setDepOpen(true);
                                }}
                              >
                                {t("versionDetail.addDependency")}
                              </Button>
                            )}
                          </div>
                          {deps.length > 0 ? (
                            <Space wrap>{deps.map((d) => renderDependencyTag(d))}</Space>
                          ) : (
                            <Typography.Text type="secondary">{t("versionDetail.dependenciesEmpty")}</Typography.Text>
                          )}
                        </div>

                        <div>
                          <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)", marginBottom: 6 }}>
                            {t("versionDetail.agentCardTitle")}
                          </div>
                          {card ? (
                            <pre
                              style={{
                                background: "var(--bg-surface-2)",
                                border: "1px solid var(--border-default)",
                                borderRadius: 6,
                                padding: 12,
                                fontSize: 11.5,
                                overflowX: "auto",
                                maxHeight: 360,
                                overflowY: "auto",
                                marginBottom: 0,
                              }}
                            >
                              {JSON.stringify(card, null, 2)}
                            </pre>
                          ) : (
                            <Spin size="small" />
                          )}
                        </div>
                      </div>
                    ),
                  };
                })}
              />
            ) : (
              <div>
                <Typography.Text type="secondary">{t("versionDetail.noFabsDeployedYet")}</Typography.Text>
                {isEditable && (
                  <div style={{ marginTop: 10, marginBottom: 18 }}>
                    <Button size="small" onClick={() => setManageFabsOpen(true)}>
                      {t("versionDetail.manageFabs")}
                    </Button>
                  </div>
                )}

                <div style={{ marginTop: 18, marginBottom: 18 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)" }}>
                      {t("versionDetail.dependenciesTitle")}
                    </div>
                    {isEditable && (
                      <Button
                        size="small"
                        onClick={() => {
                          setDepTargetFabId(null);
                          setDepOpen(true);
                        }}
                      >
                        {t("versionDetail.addDependency")}
                      </Button>
                    )}
                  </div>
                  {depsQuery.data && depsQuery.data.length > 0 ? (
                    <Space wrap>{depsQuery.data.map((d) => renderDependencyTag(d))}</Space>
                  ) : (
                    <Typography.Text type="secondary">{t("versionDetail.dependenciesEmpty")}</Typography.Text>
                  )}
                </div>

                <div>
                  <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--fg-subtle)", marginBottom: 6 }}>
                    {t("versionDetail.agentCardTitle")}
                  </div>
                  {agentCardQuery.data ? (
                    <pre
                      style={{
                        background: "var(--bg-surface-2)",
                        border: "1px solid var(--border-default)",
                        borderRadius: 6,
                        padding: 12,
                        fontSize: 11.5,
                        overflowX: "auto",
                        maxHeight: 360,
                        overflowY: "auto",
                        marginBottom: 0,
                      }}
                    >
                      {JSON.stringify(agentCardQuery.data, null, 2)}
                    </pre>
                  ) : (
                    <Spin size="small" />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", borderRadius: 8, padding: 20 }}>
          <Typography.Title level={5} style={{ marginBottom: 14 }}>
            {t("versionDetail.reviewHistoryTitle")}
          </Typography.Title>
          {reviewsQuery.data && reviewsQuery.data.length > 0 ? (
            <Space orientation="vertical" style={{ width: "100%" }} size={14}>
              {reviewsQuery.data.map((r) => (
                <div key={r.id}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontSize: 12.5, fontFamily: "monospace", color: "var(--fg-muted)" }}>
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
            <Empty description={t("versionDetail.reviewHistoryEmpty")} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </div>

      </div>

      <Modal
        title={t("versionDetail.submitModalTitle")}
        open={submitOpen}
        onCancel={() => setSubmitOpen(false)}
        onOk={() => submitForm.submit()}
        confirmLoading={submitMutation.isPending}
        okText={t("versionDetail.submitOk")}
        cancelText={t("common.cancel")}
      >
        <Form
          form={submitForm}
          layout="vertical"
          onFinish={(v) => submitMutation.mutate(v.reviewer_ids ?? [])}
        >
          <Form.Item
            label={t("versionDetail.reviewerLabel")}
            name="reviewer_ids"
            extra={t("versionDetail.reviewerExtra")}
          >
            <Select
              mode="multiple"
              placeholder={t("versionDetail.reviewerPlaceholder")}
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
        title={t("versionDetail.manageFabsModalTitle")}
        open={manageFabsOpen}
        onCancel={() => setManageFabsOpen(false)}
        onOk={() => saveFabsMutation.mutate(undefined, { onSuccess: () => setManageFabsOpen(false) })}
        confirmLoading={saveFabsMutation.isPending}
        okText={t("versionDetail.fabsSave")}
        cancelText={t("common.cancel")}
      >
        {(fabsQuery.data ?? []).map((fab) => {
          const checked = fab.id in fabUrls;
          return (
            <div key={fab.id} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <Checkbox
                checked={checked}
                disabled={!isEditable}
                onChange={(e) => {
                  setFabUrls((prev) => {
                    const next = { ...prev };
                    if (e.target.checked) next[fab.id] = next[fab.id] ?? "";
                    else delete next[fab.id];
                    return next;
                  });
                }}
              >
                {fab.fab}
              </Checkbox>
              <Input
                placeholder="https://agents.example.com/your-agent"
                value={fabUrls[fab.id] ?? ""}
                disabled={!isEditable || !checked}
                onChange={(e) => setFabUrls((prev) => ({ ...prev, [fab.id]: e.target.value }))}
                style={{ flex: 1 }}
              />
            </div>
          );
        })}
        {(fabsQuery.data ?? []).length === 0 && (
          <Typography.Text type="secondary">{t("versionDetail.fabsEmpty")}</Typography.Text>
        )}
      </Modal>

      <Modal
        title={
          depTargetFabId
            ? t("versionDetail.addDependencyModalTitleForFab", {
                fab: fabNameById.get(depTargetFabId) ?? depTargetFabId,
              })
            : t("versionDetail.addDependencyModalTitle")
        }
        open={depOpen}
        onCancel={() => setDepOpen(false)}
        onOk={() => depForm.submit()}
        confirmLoading={addDepMutation.isPending}
        okText={t("versionDetail.addOk")}
        cancelText={t("common.cancel")}
      >
        <Form
          form={depForm}
          layout="vertical"
          initialValues={{ type: "skill" }}
          onFinish={(v: { type: DependencyType; dependency_id: string }) => {
            // Encoded as "<source>:<id>" by the option values below — decode before
            // sending, the API wants source and dependency_id as separate fields.
            const [source, ...rest] = v.dependency_id.split(":");
            const isLegacy = source === "legacy";
            addDepMutation.mutate({
              type: v.type,
              source: source as DependencySource,
              dependency_id: rest.join(":"),
              // Registry items have no fab dimension (see app/services/fab_scope.py)
              // regardless of which fab tab the modal was opened from.
              fab_id: isLegacy ? depTargetFabId : null,
            });
          }}
        >
          <Form.Item label={t("common.type")} name="type" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "skill", label: "Skill" },
                { value: "mcp", label: "MCP" },
              ]}
              onChange={() => depForm.setFieldValue("dependency_id", undefined)}
            />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.type !== cur.type}>
            {({ getFieldValue }) => {
              const type: DependencyType = getFieldValue("type");
              // Which fab this dependency is scoped to comes from which fab's tab
              // the "Add Dependency" button was clicked in (depTargetFabId) — a
              // legacy skill/mcp is only offered here if it's available *there*
              // (see app/services/fab_scope.py). depTargetFabId is null when opened
              // from the no-fabs-deployed empty state, in which case there's
              // nothing to restrict against.
              const availableAt = (fabIds: Set<string>) =>
                depTargetFabId ? fabIds.has(depTargetFabId) : true;

              if (type === "mcp") {
                const mcpOptions = (mcpsQuery.data ?? [])
                  .filter((m) =>
                    availableAt(
                      new Set(m.fabs.filter((f) => f.status === "available").map((f) => f.fab_id)),
                    ),
                  )
                  .map((m) => ({ value: `legacy:${m.id}`, label: `${m.name} v${m.version}` }));
                return (
                  <Form.Item label="MCP" name="dependency_id" rules={[{ required: true }]}>
                    <Select options={mcpOptions} placeholder={t("common.select")} showSearch optionFilterProp="label" />
                  </Form.Item>
                );
              }

              const legacyOptions = (skillsQuery.data ?? [])
                .filter((s) => s.status === "available" && availableAt(new Set(s.fabs.map((f) => f.fab_id))))
                .map((s) => ({ value: `legacy:${s.id}`, label: `${s.name} v${s.version}` }));
              const registryOptions = (skillhubRegistryQuery.data?.items ?? []).map((i) => ({
                value: `registry:${i.id}`,
                label: `${i.name}${i.version ? ` v${i.version}` : ""}`,
              }));
              const groupedOptions = [
                { label: t("versionDetail.skillsUploaded"), options: legacyOptions },
                { label: t("versionDetail.skillHubSynced"), options: registryOptions },
              ];
              return (
                <Form.Item label="Skill" name="dependency_id" rules={[{ required: true }]}>
                  <Select options={groupedOptions} placeholder={t("common.select")} showSearch optionFilterProp="label" />
                </Form.Item>
              );
            }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
