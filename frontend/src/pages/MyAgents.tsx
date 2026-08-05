import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { App, Button, Form, Input, Modal, Select, Typography } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAgent, listAgents } from "../api/agents";
import type { AgentVisibility } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import AgentsTable from "../components/AgentsTable";

interface CreateAgentFormValues {
  slug: string;
  name: string;
  description?: string;
  provider?: string;
  visibility: AgentVisibility;
}

export default function MyAgents() {
  const { message } = App.useApp();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm<CreateAgentFormValues>();

  const { data: agents = [], isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: listAgents,
  });

  const createMutation = useMutation({
    mutationFn: createAgent,
    onSuccess: (agent) => {
      message.success("Agent 已建立");
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      setModalOpen(false);
      form.resetFields();
      navigate(`/agents/${agent.slug}`);
    },
    onError: () => message.error("建立失敗，slug 可能已被使用"),
  });

  const mine = agents.filter((a) => a.created_by === user?.id);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4 }}>
            My Agents
          </Typography.Title>
          <Typography.Text type="secondary">你建立的 agent。建立後即為擁有者（owner）。</Typography.Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新增 Agent
        </Button>
      </div>

      <AgentsTable agents={mine} loading={isLoading} />

      <Modal
        title="新增 Agent"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        okText="建立"
        cancelText="取消"
      >
        <Form<CreateAgentFormValues>
          form={form}
          layout="vertical"
          onFinish={(values) => createMutation.mutate(values)}
          initialValues={{ visibility: "private" }}
        >
          <Form.Item
            label="Slug"
            name="slug"
            rules={[
              { required: true, message: "請輸入 slug" },
              { pattern: /^[a-z0-9-]+$/, message: "只能用小寫英文、數字、連字號" },
            ]}
            extra="唯一識別碼，例如 invoice-extractor"
          >
            <Input placeholder="invoice-extractor" />
          </Form.Item>
          <Form.Item label="名稱" name="name" rules={[{ required: true, message: "請輸入名稱" }]}>
            <Input placeholder="Invoice Extractor" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={2} placeholder="這個 agent 是做什麼的" />
          </Form.Item>
          <Form.Item label="Provider" name="provider">
            <Input placeholder="OpenAI / Anthropic / Internal" />
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
    </div>
  );
}
