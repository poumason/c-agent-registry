import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { App, Button, Form, Input, Modal, Select, Typography } from "antd";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { createAgent, listAgents } from "../api/agents";
import type { AgentVisibility } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import AgentFormFields from "../components/AgentFormFields";
import AgentsTable from "../components/AgentsTable";

interface CreateAgentFormValues {
  slug: string;
  name: string;
  description?: string;
  provider?: string;
  visibility: AgentVisibility;
  icon_path?: string;
  category?: string[];
  hello_msg?: string;
  example_questions?: string[];
}

export default function MyAgents() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm<CreateAgentFormValues>();

  // GET /agents is now paginated (see Browse → Agents, Phase 3) — this page hasn't
  // been migrated to a paginated UI itself yet (Phase 4), so it asks for a large
  // page as a compatibility shim to keep today's "just show everything I own"
  // behavior instead of silently truncating to the default page size.
  const { data, isLoading } = useQuery({
    queryKey: ["agents", "mine"],
    queryFn: () => listAgents({ limit: 100 }),
  });
  const agents = data?.items ?? [];

  const createMutation = useMutation({
    mutationFn: createAgent,
    onSuccess: (agent) => {
      message.success(t("myAgents.createSuccess"));
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      setModalOpen(false);
      form.resetFields();
      navigate(`/agents/${agent.slug}`);
    },
    onError: () => message.error(t("myAgents.createFailed")),
  });

  const mine = agents.filter((a) => a.created_by === user?.id);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4 }}>
            My Agents
          </Typography.Title>
          <Typography.Text type="secondary">{t("myAgents.description")}</Typography.Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          {t("myAgents.addAgent")}
        </Button>
      </div>

      <AgentsTable agents={mine} loading={isLoading} />

      <Modal
        title={t("myAgents.addAgent")}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        okText={t("common.create")}
        cancelText={t("common.cancel")}
      >
        <Form<CreateAgentFormValues>
          form={form}
          layout="vertical"
          onFinish={(values) => createMutation.mutate(values)}
          initialValues={{ visibility: "private", category: ["tool"] }}
        >
          <Form.Item
            label="Slug"
            name="slug"
            rules={[
              { required: true, message: t("myAgents.slugRequired") },
              { pattern: /^[a-z0-9-]+$/, message: t("myAgents.slugPattern") },
            ]}
            extra={t("myAgents.slugExtra")}
          >
            <Input placeholder="invoice-extractor" />
          </Form.Item>
          <Form.Item label={t("common.name")} name="name" rules={[{ required: true, message: t("common.nameRequired") }]}>
            <Input placeholder="Invoice Extractor" />
          </Form.Item>
          <Form.Item label={t("common.description")} name="description">
            <Input.TextArea rows={2} placeholder={t("myAgents.descriptionPlaceholder")} />
          </Form.Item>
          <Form.Item label="Provider" name="provider">
            <Input placeholder="OpenAI / Anthropic / Internal" />
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
    </div>
  );
}
