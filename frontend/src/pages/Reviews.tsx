import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Segmented, Table, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { listMyReviews } from "../api/reviews";
import type { Review } from "../api/types";
import { ReviewResultTag } from "../components/tags";

export default function Reviews() {
  const navigate = useNavigate();
  const [pendingOnly, setPendingOnly] = useState(true);

  const { data: reviews = [], isLoading } = useQuery({
    queryKey: ["reviews-mine", pendingOnly],
    queryFn: () => listMyReviews(pendingOnly),
  });

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <div>
          <Typography.Title level={3} style={{ marginBottom: 4 }}>
            待我審核
          </Typography.Title>
          <Typography.Text type="secondary">
            指定給你的送審項目，點進去查看版本內容、核准或退回。
          </Typography.Text>
        </div>
        <Segmented
          value={pendingOnly ? "pending" : "all"}
          onChange={(v) => setPendingOnly(v === "pending")}
          options={[
            { label: "待審", value: "pending" },
            { label: "全部", value: "all" },
          ]}
        />
      </div>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={reviews}
        pagination={false}
        locale={{ emptyText: pendingOnly ? "目前沒有待審項目" : "尚無審核紀錄" }}
        onRow={(record: Review) => ({
          style: { cursor: "pointer" },
          onClick: () => navigate(`/reviews/${record.id}`),
        })}
        columns={[
          { title: "版本", dataIndex: "agent_slug" },
          { title: "優先度", dataIndex: "priority" },
          {
            title: "送審時間",
            dataIndex: "created_at",
            render: (v: string) => new Date(v).toLocaleString(),
          },
          {
            title: "狀態",
            dataIndex: "result",
            render: (result: Review["result"]) => <ReviewResultTag result={result} />,
          },
        ]}
      />
    </div>
  );
}
