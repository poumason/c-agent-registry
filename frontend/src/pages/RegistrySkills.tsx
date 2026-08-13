import { CloseOutlined, SettingOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { App, Button, Form, Modal, Select, Switch, Table, Tag, Typography } from "antd";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { assignSkillFab, listFabs, listSkills, removeSkillFab, syncSkills } from "../api/skills";
import type { Skill } from "../api/types";
import { useFormatters } from "../lib/relativeTime";

export default function RegistrySkills() {
  const { t } = useTranslation();
  const { formatDateTime } = useFormatters();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [showUnavailable, setShowUnavailable] = useState(false);
  // Skill ids whose `status` flipped in the most recent sync run — cleared on the
  // next fetch/sync so a stale highlight never lingers, same as RegistryMcps.
  const [changedIds, setChangedIds] = useState<Set<string>>(new Set());
  const [manageTarget, setManageTarget] = useState<Skill | null>(null);
  const [assignForm] = Form.useForm<{ fab_id: string }>();

  const { data: skills = [], isLoading } = useQuery({ queryKey: ["skills"], queryFn: listSkills });
  const { data: fabs = [] } = useQuery({ queryKey: ["fabs"], queryFn: listFabs });

  const syncMutation = useMutation({
    mutationFn: syncSkills,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success(t("registry.syncComplete", { available: result.available, unavailable: result.unavailable }));
      setChangedIds(new Set(result.items.filter((i) => i.changed).map((i) => i.id)));
    },
    onError: () => message.error(t("common.syncFailed")),
  });

  const assignMutation = useMutation({
    mutationFn: (fabId: string) => assignSkillFab(manageTarget!.id, fabId),
    onSuccess: () => {
      message.success(t("registry.fabAssignSuccess"));
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      assignForm.resetFields();
    },
    onError: () => message.error(t("registry.fabAssignFailed")),
  });

  const removeMutation = useMutation({
    mutationFn: (fabId: string) => removeSkillFab(manageTarget!.id, fabId),
    onSuccess: () => {
      message.success(t("registry.fabRemoveSuccess"));
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
    onError: () => message.error(t("common.removeFailed")),
  });

  const lastSyncedAt = useMemo(() => {
    const timestamps = skills.map((s) => s.last_synced_at).filter((v): v is string => !!v);
    if (timestamps.length === 0) return null;
    return timestamps.reduce((a, b) => (a > b ? a : b));
  }, [skills]);

  const availableCount = skills.filter((s) => s.status === "available").length;
  const unavailableCount = skills.length - availableCount;
  const visibleSkills = showUnavailable ? skills : skills.filter((s) => s.status === "available");

  const liveManageTarget = manageTarget ? skills.find((s) => s.id === manageTarget.id) ?? null : null;
  const unassignedFabs = liveManageTarget
    ? fabs.filter((f) => !liveManageTarget.fabs.some((sf) => sf.fab_id === f.id))
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
            Registry · Skill
          </Typography.Title>
          <Typography.Text type="secondary">{t("registry.skillDescription")}</Typography.Text>
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
        dataSource={visibleSkills}
        pagination={false}
        rowClassName={(s: Skill) => (changedIds.has(s.id) ? "row-recently-changed" : "")}
        columns={[
          {
            title: t("common.name"),
            dataIndex: "name",
            render: (_: string, r: Skill) => (
              <div>
                <div style={{ fontWeight: 600 }}>{r.name}</div>
                <div style={{ color: "var(--fg-subtle)", fontSize: 12 }}>v{r.version}</div>
              </div>
            ),
          },
          { title: t("common.category"), dataIndex: "category", render: (v: string | null) => v ?? "—" },
          {
            title: t("common.status"),
            dataIndex: "status",
            render: (s: Skill["status"], row: Skill) => (
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {s === "available" ? (
                  <Tag color="green">{t("registry.available")}</Tag>
                ) : (
                  <Tag color="red">{t("registry.unavailable")}</Tag>
                )}
                {changedIds.has(row.id) && <Tag color="gold">{t("registry.recentlyChanged")}</Tag>}
              </span>
            ),
          },
          {
            title: t("registry.fabsColumn"),
            dataIndex: "fabs",
            render: (fabsCol: Skill["fabs"]) => fabsCol.length,
          },
          {
            title: t("common.updatedAt"),
            dataIndex: "updated_at",
            render: (v: string) => formatDateTime(v),
          },
          {
            title: "",
            key: "actions",
            render: (_: unknown, r: Skill) => (
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
                    <Tag>{fabs.find((fab) => fab.id === f.fab_id)?.fab ?? f.fab_id}</Tag>
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
              onFinish={(v) => assignMutation.mutate(v.fab_id)}
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
