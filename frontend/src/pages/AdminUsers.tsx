import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { App, Button, Form, Input, Modal, Select, Switch, Table, Typography } from "antd";
import { useState } from "react";
import { createUser, listUsers, updateUser } from "../api/users";
import type { CreateUserInput } from "../api/users";
import type { User } from "../api/types";
import { UserRoleTag } from "../components/tags";

export default function AdminUsers() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm<CreateUserInput>();

  const { data: users = [], isLoading } = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      message.success("使用者已建立");
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setCreateOpen(false);
      form.resetFields();
    },
    onError: () => message.error("建立失敗，email 可能已被使用"),
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: User["status"] }) =>
      updateUser(id, { status }),
    onSuccess: () => {
      message.success("已更新狀態");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: () => message.error("更新失敗"),
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4 }}>
            使用者管理
          </Typography.Title>
          <Typography.Text type="secondary">
            只有系統角色為 admin 的使用者能看到這一頁。新帳號無法自行註冊，只能由 admin 建立。
          </Typography.Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          新增使用者
        </Button>
      </div>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={users}
        pagination={false}
        columns={[
          { title: "姓名", dataIndex: "name" },
          { title: "Email", dataIndex: "email" },
          { title: "角色", dataIndex: "role", render: (r: User["role"]) => <UserRoleTag role={r} /> },
          {
            title: "狀態",
            dataIndex: "status",
            render: (s: User["status"], record: User) => (
              <Switch
                checked={s === "active"}
                checkedChildren="active"
                unCheckedChildren="disabled"
                onChange={(checked) =>
                  toggleStatusMutation.mutate({ id: record.id, status: checked ? "active" : "disabled" })
                }
              />
            ),
          },
          {
            title: "加入時間",
            dataIndex: "created_at",
            render: (v: string) => new Date(v).toLocaleDateString(),
          },
        ]}
      />

      <Modal
        title="新增使用者"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        okText="建立"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)} initialValues={{ role: "member" }}>
          <Form.Item label="姓名" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Email" name="email" rules={[{ required: true, type: "email" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="初始密碼" name="password" rules={[{ required: true, min: 8, message: "至少 8 個字元" }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item label="系統角色" name="role" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "member", label: "member" },
                { value: "reviewer", label: "reviewer" },
                { value: "admin", label: "admin" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
