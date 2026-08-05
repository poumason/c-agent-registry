import { PlusOutlined, UploadOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App,
  Button,
  Form,
  Input,
  Modal,
  Table,
  Tabs,
  Typography,
  Upload,
} from "antd";
import type { UploadFile } from "antd/es/upload/interface";
import { useState } from "react";
import { createMcp, createSkill, listMcps, listSkills } from "../api/skills";
import type { CreateMcpInput, CreateSkillInput } from "../api/skills";

export default function Skills() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [skillModalOpen, setSkillModalOpen] = useState(false);
  const [mcpModalOpen, setMcpModalOpen] = useState(false);
  const [skillForm] = Form.useForm<Omit<CreateSkillInput, "file"> & { file: UploadFile[] }>();
  const [mcpForm] = Form.useForm<CreateMcpInput>();

  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: listSkills });
  const mcpsQuery = useQuery({ queryKey: ["mcps"], queryFn: listMcps });

  const createSkillMutation = useMutation({
    mutationFn: createSkill,
    onSuccess: () => {
      message.success("Skill 已建立");
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      setSkillModalOpen(false);
      skillForm.resetFields();
    },
    onError: () => message.error("建立失敗"),
  });

  const createMcpMutation = useMutation({
    mutationFn: createMcp,
    onSuccess: () => {
      message.success("MCP 已建立");
      queryClient.invalidateQueries({ queryKey: ["mcps"] });
      setMcpModalOpen(false);
      mcpForm.resetFields();
    },
    onError: () => message.error("建立失敗"),
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4 }}>
            Skills &amp; MCP
          </Typography.Title>
          <Typography.Text type="secondary">可重複使用、跨 agent 掛載的能力登錄。</Typography.Text>
        </div>
      </div>

      <Tabs
        defaultActiveKey="skills"
        items={[
          {
            key: "skills",
            label: "Skills",
            children: (
              <>
                <Button icon={<PlusOutlined />} onClick={() => setSkillModalOpen(true)} style={{ marginBottom: 12 }}>
                  新增 Skill
                </Button>
                <Table
                  rowKey="id"
                  loading={skillsQuery.isLoading}
                  dataSource={skillsQuery.data ?? []}
                  pagination={false}
                  columns={[
                    {
                      title: "名稱",
                      dataIndex: "name",
                      render: (_: string, r) => (
                        <div>
                          <div style={{ fontWeight: 600 }}>{r.name}</div>
                          <div style={{ color: "#9AA0AC", fontSize: 12 }}>v{r.version}</div>
                        </div>
                      ),
                    },
                    { title: "分類", dataIndex: "category", render: (v: string | null) => v ?? "—" },
                    {
                      title: "更新時間",
                      dataIndex: "updated_at",
                      render: (v: string) => new Date(v).toLocaleString(),
                    },
                  ]}
                />
              </>
            ),
          },
          {
            key: "mcp",
            label: "MCP",
            children: (
              <>
                <Button icon={<PlusOutlined />} onClick={() => setMcpModalOpen(true)} style={{ marginBottom: 12 }}>
                  新增 MCP
                </Button>
                <Table
                  rowKey="id"
                  loading={mcpsQuery.isLoading}
                  dataSource={mcpsQuery.data ?? []}
                  pagination={false}
                  columns={[
                    {
                      title: "名稱",
                      dataIndex: "name",
                      render: (_: string, r) => (
                        <div>
                          <div style={{ fontWeight: 600 }}>{r.name}</div>
                          <div style={{ color: "#9AA0AC", fontSize: 12 }}>v{r.version}</div>
                        </div>
                      ),
                    },
                    {
                      title: "Host",
                      dataIndex: "host",
                      render: (v: string) => <span style={{ fontFamily: "monospace", fontSize: 12.5 }}>{v}</span>,
                    },
                    {
                      title: "更新時間",
                      dataIndex: "updated_at",
                      render: (v: string) => new Date(v).toLocaleString(),
                    },
                  ]}
                />
              </>
            ),
          },
        ]}
      />

      <Modal
        title="新增 Skill"
        open={skillModalOpen}
        onCancel={() => setSkillModalOpen(false)}
        onOk={() => skillForm.submit()}
        confirmLoading={createSkillMutation.isPending}
        okText="上傳"
        cancelText="取消"
      >
        <Form
          form={skillForm}
          layout="vertical"
          onFinish={(v) => {
            const file = v.file?.[0]?.originFileObj as File | undefined;
            if (!file) {
              message.error("請選擇檔案");
              return;
            }
            createSkillMutation.mutate({ ...v, file });
          }}
        >
          <Form.Item label="名稱" name="name" rules={[{ required: true }]}>
            <Input placeholder="pdf-ocr-extract" />
          </Form.Item>
          <Form.Item label="版本" name="version" rules={[{ required: true }]}>
            <Input placeholder="1.0.0" />
          </Form.Item>
          <Form.Item label="分類" name="category">
            <Input placeholder="extraction" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item
            label="檔案"
            name="file"
            valuePropName="fileList"
            getValueFromEvent={(e) => e?.fileList}
            rules={[{ required: true, message: "請選擇檔案" }]}
          >
            <Upload beforeUpload={() => false} maxCount={1}>
              <Button icon={<UploadOutlined />}>選擇檔案</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新增 MCP"
        open={mcpModalOpen}
        onCancel={() => setMcpModalOpen(false)}
        onOk={() => mcpForm.submit()}
        confirmLoading={createMcpMutation.isPending}
        okText="建立"
        cancelText="取消"
      >
        <Form form={mcpForm} layout="vertical" onFinish={(v) => createMcpMutation.mutate(v)}>
          <Form.Item label="名稱" name="name" rules={[{ required: true }]}>
            <Input placeholder="finance-db-mcp" />
          </Form.Item>
          <Form.Item label="版本" name="version" rules={[{ required: true }]}>
            <Input placeholder="1.0.0" />
          </Form.Item>
          <Form.Item label="Host" name="host" rules={[{ required: true }]}>
            <Input placeholder="mcp://finance.internal:8443" />
          </Form.Item>
          <Form.Item label="分類" name="category">
            <Input placeholder="finance" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
