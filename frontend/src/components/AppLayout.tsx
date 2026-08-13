import {
  AppstoreOutlined,
  BarChartOutlined,
  CompassOutlined,
  DatabaseOutlined,
  DownOutlined,
  GlobalOutlined,
  LogoutOutlined,
  MenuOutlined,
  UserOutlined,
  UsergroupAddOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Drawer, Dropdown, Grid, Layout, Menu, Tag } from "antd";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { SupportedLanguage } from "../i18n";
import { ThemeToggle } from "./ThemeToggle";

function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current: SupportedLanguage = i18n.language.startsWith("en") ? "en" : "zh";

  return (
    <Dropdown
      menu={{
        selectedKeys: [current],
        items: [
          { key: "zh", label: t("nav.languageZh") },
          { key: "en", label: t("nav.languageEn") },
        ],
        onClick: ({ key }) => i18n.changeLanguage(key),
      }}
    >
      <Button type="text" icon={<GlobalOutlined />} aria-label={t("nav.language")}>
        {current === "zh" ? t("nav.languageZh") : t("nav.languageEn")}
      </Button>
    </Dropdown>
  );
}

const { Header, Sider, Content } = Layout;

function Brand() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "18px 18px 12px" }}>
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: 7,
          background: "var(--color-brand)",
          color: "var(--fg-on-brand)",
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
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = Grid.useBreakpoint();
  const isMobile = screens.lg === false;
  const [drawerOpen, setDrawerOpen] = useState(false);

  const selectedKey = useMemo(() => {
    const path = location.pathname;
    if (path.startsWith("/my-agents") || path.startsWith("/agents/")) return "my-agents";
    if (path.startsWith("/review-queue")) return "review-queue";
    if (path.startsWith("/admin/review-summary")) return "review-summary";
    if (path.startsWith("/registry/skills")) return "registry-skills";
    if (path.startsWith("/registry/mcps")) return "registry-mcps";
    if (path.startsWith("/registry/models")) return "registry-models";
    if (path.startsWith("/admin/fabs")) return "admin-fabs";
    if (path.startsWith("/admin/users")) return "admin-users";
    if (path.startsWith("/admin/agent-summary")) return "admin-agent-summary";
    if (path.startsWith("/admin/agents")) return "admin-agents";
    if (path.startsWith("/admin/user-summary")) return "admin-user-summary";
    if (path.startsWith("/admin/agent-templates")) return "admin-agent-templates";
    if (path.startsWith("/admin/stats")) return "admin-stats";
    return "browse";
  }, [location.pathname]);

  if (!user) return null;
  const initial = user.name.slice(0, 1).toUpperCase();

  const go = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const menuItems = [
    { key: "browse", icon: <CompassOutlined />, label: t("nav.browse"), onClick: () => go("/") },
    {
      key: "agent-mgmt",
      icon: <AppstoreOutlined />,
      label: t("nav.agentManagement"),
      children: [{ key: "my-agents", label: t("nav.myAgents"), onClick: () => go("/my-agents") }],
    },
    {
      key: "reviews",
      icon: <UsergroupAddOutlined />,
      label: t("nav.reviews"),
      children: [
        { key: "review-queue", label: t("nav.reviewQueue"), onClick: () => go("/review-queue") },
        ...(user.role === "admin"
          ? [{ key: "review-summary", label: t("nav.reviewSummary"), onClick: () => go("/admin/review-summary") }]
          : []),
      ],
    },
    ...(user.role === "admin"
      ? [
          {
            key: "admin",
            icon: <UserOutlined />,
            label: t("nav.governance"),
            children: [
              { key: "admin-users", label: t("nav.users"), onClick: () => go("/admin/users") },
              { key: "admin-user-summary", label: t("nav.userSummary"), onClick: () => go("/admin/user-summary") },
              { key: "admin-agents", label: t("nav.agents"), onClick: () => go("/admin/agents") },
              { key: "admin-agent-summary", label: t("nav.agentSummary"), onClick: () => go("/admin/agent-summary") },
              { key: "admin-fabs", label: t("nav.fabs"), onClick: () => go("/admin/fabs") },
            ],
          },
          {
            key: "registry",
            icon: <DatabaseOutlined />,
            label: t("nav.registry"),
            children: [
              { key: "admin-agent-templates", label: t("nav.agentTemplates"), onClick: () => go("/admin/agent-templates") },
              { key: "registry-skills", label: t("nav.skill"), onClick: () => go("/registry/skills") },
              { key: "registry-mcps", label: t("nav.mcp"), onClick: () => go("/registry/mcps") },
              { key: "registry-models", label: t("nav.model"), onClick: () => go("/registry/models") },
            ],
          },
          {
            key: "reports",
            icon: <BarChartOutlined />,
            label: t("nav.reports"),
            children: [{ key: "admin-stats", label: t("nav.statistics"), onClick: () => go("/admin/stats") }],
          },
        ]
      : []),
  ];

  const nav = (
    <Menu
      mode="inline"
      selectedKeys={[selectedKey]}
      defaultOpenKeys={["agent-mgmt", "reviews", "admin"]}
      items={menuItems}
      style={{ border: "none" }}
    />
  );

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {!isMobile && (
        <Sider width={224} theme="light" style={{ borderRight: "1px solid var(--border-default)" }}>
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
            background: "var(--bg-surface)",
            borderBottom: "1px solid var(--border-default)",
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
              aria-label={t("nav.openMenu")}
            />
          ) : (
            <span />
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <ThemeToggle />
            <LanguageSwitcher />
            <Dropdown
              menu={{
                items: [
                  {
                    key: "logout",
                    icon: <LogoutOutlined />,
                    label: t("nav.logout"),
                    onClick: () => {
                      logout();
                      navigate("/login");
                    },
                  },
                ],
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 9, cursor: "pointer" }}>
                <Avatar size={26} style={{ background: "var(--color-brand-tint)", color: "var(--fg-on-brand-tint)" }}>
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
                <DownOutlined style={{ fontSize: 11, color: "var(--fg-subtle)" }} />
              </div>
            </Dropdown>
          </div>
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
