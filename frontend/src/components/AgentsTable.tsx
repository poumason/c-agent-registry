import { Avatar, Table } from "antd";
import { useNavigate } from "react-router-dom";
import type { Agent } from "../api/types";
import { VisibilityTag } from "./tags";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "剛剛";
  if (mins < 60) return `${mins} 分鐘前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小時前`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} 天前`;
  return new Date(iso).toLocaleDateString();
}

export default function AgentsTable({ agents, loading }: { agents: Agent[]; loading: boolean }) {
  const navigate = useNavigate();

  return (
    <Table
      loading={loading}
      dataSource={agents}
      rowKey="id"
      pagination={false}
      onRow={(record) => ({
        style: { cursor: "pointer" },
        onClick: () => navigate(`/agents/${record.slug}`),
      })}
      scroll={{ x: 640 }}
      columns={[
        {
          title: "名稱",
          dataIndex: "name",
          render: (_: string, record: Agent) => (
            <div>
              <div style={{ fontWeight: 600 }}>{record.name}</div>
              <div style={{ color: "#9AA0AC", fontSize: 12 }}>{record.slug}</div>
            </div>
          ),
        },
        {
          title: "Visibility",
          dataIndex: "visibility",
          render: (v: Agent["visibility"]) => <VisibilityTag visibility={v} />,
        },
        { title: "Provider", dataIndex: "provider", render: (p: string | null) => p ?? "—" },
        {
          title: "更新時間",
          dataIndex: "updated_at",
          render: (v: string) => timeAgo(v),
        },
      ]}
      locale={{ emptyText: "目前沒有 agent" }}
      style={{ background: "#fff" }}
    />
  );
}

export function AvatarInitial({ name }: { name: string }) {
  return (
    <Avatar size={22} style={{ background: "#EEF0FE", color: "#4338CA", fontSize: 10 }}>
      {name.slice(0, 1).toUpperCase()}
    </Avatar>
  );
}
