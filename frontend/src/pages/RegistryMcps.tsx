import { CloseOutlined, SettingOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Empty, Form, Modal, Select, Switch, Table, Tag, Typography, App, Input } from "antd";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { assignMcpFab, listFabs, listMcps, removeMcpFab, syncMcps } from "../api/skills";
import type { AssignMcpFabInput } from "../api/skills";
import type { Mcp, McpFab } from "../api/types";
import { useFormatters } from "../lib/relativeTime";

// Keyed by `${mcp_id}:${fab_id}` — set right after a sync completes, so the table can
// highlight exactly the fab rows that sync just flipped, and cleared on the next
// fetch/sync so a stale highlight never lingers.
type ChangedKeys = Set<string>;

function fabKey(mcpId: string, fabId: string): string {
  return `${mcpId}:${fabId}`;
}

export default function RegistryMcps() {
  const { t } = useTranslation();
  const { formatDateTime } = useFormatters();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [showUnavailable, setShowUnavailable] = useState(false);
  const [changedKeys, setChangedKeys] = useState<ChangedKeys>(new Set());
  const [manageTarget, setManageTarget] = useState<Mcp | null>(null);
  const [assignForm] = Form.useForm<AssignMcpFabInput>();

  const { data: mcps = [], isLoading } = useQuery({ queryKey: ["mcps"], queryFn: listMcps });
  const { data: fabs = [] } = useQuery({ queryKey: ["fabs"], queryFn: listFabs });

  const syncMutation = useMutation({
    mutationFn: syncMcps,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["mcps"] });
      message.success(t("registry.syncComplete", { available: result.available, unavailable: result.unavailable }));
      const next: ChangedKeys = new Set();
      for (const item of result.items) {
        for (const fab of item.fabs) {
          if (fab.changed) next.add(fabKey(item.id, fab.fab_id));
        }
      }
      setChangedKeys(next);
    },
    onError: () => message.error(t("common.syncFailed")),
  });

  const assignMutation = useMutation({
    mutationFn: (input: AssignMcpFabInput) => assignMcpFab(manageTarget!.id, input),
    onSuccess: () => {
      message.success(t("registry.fabAssignSuccess"));
      queryClient.invalidateQueries({ queryKey: ["mcps"] });
      assignForm.resetFields();
    },
    onError: () => message.error(t("registry.fabAssignFailed")),
  });

  const removeMutation = useMutation({
    mutationFn: (fabId: string) => removeMcpFab(manageTarget!.id, fabId),
    onSuccess: () => {
      message.success(t("registry.fabRemoveSuccess"));
      queryClient.invalidateQueries({ queryKey: ["mcps"] });
    },
    onError: () => message.error(t("common.removeFailed")),
  });

  const allFabs = useMemo(() => mcps.flatMap((m) => m.fabs), [mcps]);
  const lastSyncedAt = useMemo(() => {
    const timestamps = allFabs.map((f) => f.last_synced_at).filter((v): v is string => !!v);
    if (timestamps.length === 0) return null;
    return timestamps.reduce((a, b) => (a > b ? a : b));
  }, [allFabs]);

  const availableCount = allFabs.filter((f) => f.status === "available").length;
  const unavailableCount = allFabs.length - availableCount;
  // An MCP is visible if it has at least one fab matching the current filter (an MCP
  // with zero fabs at all is always shown — "show unavailable" only hides ones that
  // are entirely unavailable, not ones that were never deployed anywhere).
  const visibleMcps = showUnavailable
    ? mcps
    : mcps.filter((m) => m.fabs.length === 0 || m.fabs.some((f) => f.status === "available"));

  // Re-derive the manage-modal's target from the live query data (rather than the
  // stale snapshot captured when the modal opened) so assign/remove immediately
  // reflect in the "already assigned" list without closing the modal.
  const liveManageTarget = manageTarget ? mcps.find((m) => m.id === manageTarget.id) ?? null : null;
  const unassignedFabs = liveManageTarget
    ? fabs.filter((f) => !liveManageTarget.fabs.some((mf) => mf.fab_id === f.id))
    : [];

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4 }}>
            Registry · MCP
          </Typography.Title>
          <Typography.Text type="secondary">{t("registry.mcpDescription")}</Typography.Text>
        </div>
        <Button
          icon={<SyncOutlined spin={syncMutation.isPending} />}
          loading={syncMutation.isPending}
          onClick={() => syncMutation.mutate()}
        >
          {t("registry.sync")}
        </Button>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
          background: "var(--bg-surface-2)",
          border: "1px solid var(--border-default)",
          borderRadius: 8,
          padding: "10px 14px",
          marginBottom: 16,
          fontSize: 13,
        }}
      >
        <span style={{ color: "var(--fg-muted)" }}>
          {lastSyncedAt ? t("registry.lastSynced", { date: formatDateTime(lastSyncedAt) }) : t("common.notSyncedYet")}
          {" · "}
          {t("registry.availableCount", { available: availableCount, unavailable: unavailableCount })}
        </span>
        <Switch
          checkedChildren={t("registry.showUnavailable")}
          unCheckedChildren={t("registry.showAvailableOnly")}
          checked={showUnavailable}
          onChange={setShowUnavailable}
        />
      </div>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={visibleMcps}
        pagination={false}
        expandable={{
          defaultExpandAllRows: true,
          rowExpandable: (r: Mcp) => r.fabs.length > 0,
          expandedRowRender: (r: Mcp) => {
            const shownFabs = showUnavailable ? r.fabs : r.fabs.filter((f) => f.status === "available");
            if (shownFabs.length === 0) {
              return <Empty description={t("registry.noFabs")} image={Empty.PRESENTED_IMAGE_SIMPLE} />;
            }
            return (
              <Table<McpFab>
                rowKey="fab_id"
                size="small"
                pagination={false}
                dataSource={shownFabs}
                rowClassName={(f) => (changedKeys.has(fabKey(r.id, f.fab_id)) ? "row-recently-changed" : "")}
                columns={[
                  { title: t("registry.fabsColumn"), dataIndex: "fab_id" },
                  {
                    title: t("registry.hostColumn"),
                    dataIndex: "host",
                    render: (v: string) => <span style={{ fontFamily: "monospace", fontSize: 12.5 }}>{v}</span>,
                  },
                  {
                    title: t("common.status"),
                    dataIndex: "status",
                    render: (s: McpFab["status"], row: McpFab) => (
                      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        {s === "available" ? (
                          <Tag color="green">{t("registry.available")}</Tag>
                        ) : (
                          <Tag color="red">{t("registry.unavailable")}</Tag>
                        )}
                        {changedKeys.has(fabKey(r.id, row.fab_id)) && (
                          <Tag color="gold">{t("registry.recentlyChanged")}</Tag>
                        )}
                      </span>
                    ),
                  },
                  {
                    title: t("common.updatedAt"),
                    dataIndex: "last_synced_at",
                    render: (v: string | null) => (v ? formatDateTime(v) : t("common.notSyncedYet")),
                  },
                ]}
              />
            );
          },
        }}
        columns={[
          {
            title: t("common.name"),
            dataIndex: "name",
            render: (_: string, r: Mcp) => (
              <div>
                <div style={{ fontWeight: 600 }}>{r.name}</div>
                <div style={{ color: "var(--fg-subtle)", fontSize: 12 }}>v{r.version}</div>
              </div>
            ),
          },
          { title: t("common.category"), dataIndex: "category", render: (v: string | null) => v ?? "—" },
          {
            title: t("registry.fabCount"),
            dataIndex: "fabs",
            render: (fabsCol: McpFab[]) => `${fabsCol.filter((f) => f.status === "available").length} / ${fabsCol.length}`,
          },
          {
            title: "",
            key: "actions",
            render: (_: unknown, r: Mcp) => (
              <Button size="small" icon={<SettingOutlined />} onClick={() => setManageTarget(r)}>
                {t("registry.manageFabs")}
              </Button>
            ),
          },
        ]}
      />

      <Modal
        title={liveManageTarget ? t("registry.manageFabsTitle", { name: liveManageTarget.name }) : ""}
        open={!!manageTarget}
        onCancel={() => setManageTarget(null)}
        footer={null}
      >
        {liveManageTarget && (
          <>
            {liveManageTarget.fabs.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                {liveManageTarget.fabs.map((f) => (
                  <div
                    key={f.fab_id}
                    style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, padding: "6px 0" }}
                  >
                    <span style={{ fontSize: 13 }}>
                      <Tag>{fabs.find((fab) => fab.id === f.fab_id)?.fab ?? f.fab_id}</Tag>
                      <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--fg-subtle)" }}>{f.host}</span>
                    </span>
                    <Button
                      size="small"
                      type="text"
                      danger
                      icon={<CloseOutlined />}
                      loading={removeMutation.isPending}
                      onClick={() => removeMutation.mutate(f.fab_id)}
                      aria-label={t("common.remove")}
                    />
                  </div>
                ))}
              </div>
            )}
            <Form
              form={assignForm}
              layout="vertical"
              onFinish={(v) => assignMutation.mutate(v)}
              disabled={unassignedFabs.length === 0}
            >
              <Form.Item label={t("registry.fabLabel")} name="fab_id" rules={[{ required: true }]}>
                <Select
                  placeholder={
                    unassignedFabs.length === 0 ? t("registry.allFabsAssigned") : t("common.select")
                  }
                  options={unassignedFabs.map((f) => ({ value: f.id, label: f.fab }))}
                />
              </Form.Item>
              <Form.Item label={t("registry.hostColumn")} name="host" rules={[{ required: true }]}>
                <Input placeholder="https://finance.internal:8443" />
              </Form.Item>
              <Button htmlType="submit" type="primary" loading={assignMutation.isPending}>
                {t("registry.assignFab")}
              </Button>
            </Form>
          </>
        )}
      </Modal>
    </div>
  );
}
