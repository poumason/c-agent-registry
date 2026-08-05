import { LockOutlined, MailOutlined, SafetyOutlined } from "@ant-design/icons";
import { Alert, Button, Divider, Form, Input, Typography } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ssoLoginUrl } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

interface LoginFormValues {
  email: string;
  password: string;
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onFinish(values: LoginFormValues) {
    setError(null);
    setSubmitting(true);
    try {
      await login(values.email, values.password);
      navigate("/", { replace: true });
    } catch {
      setError("帳號或密碼錯誤");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "radial-gradient(600px 400px at 15% 10%, #EEF0FE, transparent 60%), #F6F7FA",
        padding: 24,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 380,
          background: "#fff",
          border: "1px solid #E4E6EC",
          borderRadius: 12,
          boxShadow: "0 8px 24px rgba(20, 24, 38, 0.12)",
          padding: "36px 32px 28px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "#4338CA",
              color: "#fff",
              fontWeight: 700,
              fontSize: 15,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            AR
          </div>
          <div>
            <div style={{ fontWeight: 650, fontSize: 16 }}>Agent Registry</div>
            <div style={{ fontSize: 12, color: "#9AA0AC" }}>內部 agent 建立與審核平台</div>
          </div>
        </div>

        <Typography.Title level={4} style={{ marginBottom: 4 }}>
          登入
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ fontSize: 13, marginBottom: 24 }}>
          使用你的帳號密碼，或透過公司 SSO 登入。
        </Typography.Paragraph>

        {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            label="Email"
            name="email"
            rules={[{ required: true, message: "請輸入 email" }]}
          >
            <Input prefix={<MailOutlined />} placeholder="you@company.com" size="large" />
          </Form.Item>
          <Form.Item
            label="密碼"
            name="password"
            rules={[{ required: true, message: "請輸入密碼" }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="••••••••" size="large" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block size="large" loading={submitting}>
            登入
          </Button>
        </Form>

        <Divider plain style={{ fontSize: 12, color: "#9AA0AC" }}>
          或
        </Divider>

        <Button
          block
          size="large"
          icon={<SafetyOutlined />}
          onClick={() => {
            window.location.href = ssoLoginUrl();
          }}
        >
          使用 SSO 登入
        </Button>
      </div>
    </div>
  );
}
