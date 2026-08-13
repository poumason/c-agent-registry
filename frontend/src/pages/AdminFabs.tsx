import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { App, Button, Form, Input, Modal, Table, Typography } from "antd";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { createFab, listFabs } from "../api/skills";
import type { CreateFabInput } from "../api/skills";

export default function AdminFabs() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm<CreateFabInput>();

  const { data: fabs = [], isLoading } = useQuery({ queryKey: ["fabs"], queryFn: listFabs });

  const createMutation = useMutation({
    mutationFn: createFab,
    onSuccess: () => {
      message.success(t("registry.createSuccess", { item: "Fab" }));
      queryClient.invalidateQueries({ queryKey: ["fabs"] });
      setCreateOpen(false);
      form.resetFields();
    },
    onError: () => message.error(t("common.createFailed")),
  });

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
        <Typography.Title level={3} style={{ marginBottom: 4 }}>
          {t("nav.fabs")}
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          {t("registry.addFab")}
        </Button>
      </div>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={fabs}
        pagination={false}
        columns={[{ title: t("registry.fabLabel"), dataIndex: "fab" }]}
      />

      <Modal
        title={t("registry.addFab")}
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        okText={t("common.create")}
        cancelText={t("common.cancel")}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item label={t("registry.fabLabel")} name="fab" rules={[{ required: true }]}>
            <Input placeholder={t("registry.fabNamePlaceholder")} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
