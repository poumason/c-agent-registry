import {
  AppstoreOutlined,
  CompassOutlined,
  DownOutlined,
  LogoutOutlined,
  MenuOutlined,
  ToolOutlined,
  UserOutlined,
  UsergroupAddOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Drawer, Dropdown, Grid, Layout, Menu, Tag } from "antd";
import { useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const { Header, Sider, Content } = Layout;

function Brand() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "18px 18px 12px" }}>
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: 7,
          background: "#4338CA",
          color: "#fff",
          fontWeight: 700,
          fontSize: 13,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        AR
      </div>
      <div style={{ fontWeight: 650, fontSize: 14.5 }}>Agent Registry</div>
    </div>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = Grid.useBreakpoint();
  const isMobile = screens.lg === false;
  const [drawerOpen, setDrawerOpen] = useState(false);

  const selectedKey = useMemo(() => {
    const path = location.pathname;
    if (path.startsWith("/my-agents") || path.startsWith("/agents/")) return "my-agents";
    if (path.startsWith("/reviews")) return "reviews";
    if (path.startsWith("/skills")) return "skills";
    if (path.startsWith("/admin/users")) return "admin-users";
    return "browse";
  }, [location.pathname]);

  if (!user) return null;
  const initial = user.name.slice(0, 1).toUpperCase();

  const go = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const menuItems = [
    { key: "browse", icon: <CompassOutlined />, label: "Browse", onClick: () => go("/") },
    {
      key: "agent-mgmt",
      icon: <AppstoreOutlined />,
      label: "Agent Management",
      children: [{ key: "my-agents", label: "My Agents", onClick: () => go("/my-agents") }],
    },
    {
      key: "reviews",
      icon: <UsergroupAddOutlined />,
      label: "Reviews",
      onClick: () => go("/reviews"),
    },
    {
      key: "skills",
      icon: <ToolOutlined />,
      label: "Skills & MCP",
      onClick: () => go("/skills"),
    },
    ...(user.role === "admin"
      ? [
          {
            key: "admin",
            icon: <UserOutlined />,
            label: "Admin",
            children: [
              { key: "admin-users", label: "使用者管理", onClick: () => go("/admin/users") },
            ],
          },
        ]
      : []),
  ];

  const nav = (
    <Menu
      mode="inline"
      selectedKeys={[selectedKey]}
      defaultOpenKeys={["agent-mgmt", "admin"]}
      items={menuItems}
      style={{ border: "none" }}
    />
  );

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {!isMobile && (
        <Sider width={224} theme="light" style={{ borderRight: "1px solid #E4E6EC" }}>
          <Brand />
          {nav}
        </Sider>
      )}
      {isMobile && (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          closable={false}
          size={240}
          styles={{ body: { padding: 0 } }}
        >
          <Brand />
          {nav}
        </Drawer>
      )}
      <Layout style={{ minWidth: 0 }}>
        <Header
          style={{
            background: "#fff",
            borderBottom: "1px solid #E4E6EC",
            padding: "0 16px 0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
          }}
        >
          {isMobile ? (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setDrawerOpen(true)}
              aria-label="開啟選單"
            />
          ) : (
            <span />
          )}
          <Dropdown
            menu={{
              items: [
                {
                  key: "logout",
                  icon: <LogoutOutlined />,
                  label: "登出",
                  onClick: () => {
                    logout();
                    navigate("/login");
                  },
                },
              ],
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 9, cursor: "pointer" }}>
              <Avatar size={26} style={{ background: "#EEF0FE", color: "#4338CA" }}>
                {initial}
              </Avatar>
              {!isMobile && (
                <div style={{ lineHeight: 1.3 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{user.name}</div>
                  <Tag
                    color={user.role === "admin" ? "blue" : user.role === "reviewer" ? "cyan" : "default"}
                    style={{ marginTop: 1, fontSize: 10, lineHeight: "14px", padding: "0 5px" }}
                  >
                    {user.role}
                  </Tag>
                </div>
              )}
              <DownOutlined style={{ fontSize: 11, color: "#9AA0AC" }} />
            </div>
          </Dropdown>
        </Header>
        <Content
          style={{
            padding: isMobile ? "18px 16px 40px" : "26px 28px 60px",
            maxWidth: 1180,
            width: "100%",
            margin: "0 auto",
            minWidth: 0,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
