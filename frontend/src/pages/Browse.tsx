import { useQuery } from "@tanstack/react-query";
import { Segmented, Typography } from "antd";
import { useState } from "react";
import { listAgents } from "../api/agents";
import AgentsTable from "../components/AgentsTable";

export default function Browse() {
  const [filter, setFilter] = useState<"public" | "all">("public");
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: listAgents,
  });

  const visible = filter === "public" ? agents.filter((a) => a.visibility === "public") : agents;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Typography.Title level={3} style={{ marginBottom: 4 }}>
          Browse
        </Typography.Title>
        <Typography.Text type="secondary">瀏覽你有權限檢視的 agent。</Typography.Text>
      </div>

      <Segmented
        value={filter}
        onChange={(v) => setFilter(v as "public" | "all")}
        options={[
          { label: "Public", value: "public" },
          { label: "全部我看得到的", value: "all" },
        ]}
        style={{ marginBottom: 16 }}
      />

      <AgentsTable agents={visible} loading={isLoading} />
    </div>
  );
}
