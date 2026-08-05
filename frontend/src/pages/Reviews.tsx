import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { App, Button, Space, Table, Typography } from "antd";
import { Link } from "react-router-dom";
import { decideReview, listMyReviews } from "../api/reviews";
import type { Review } from "../api/types";

export default function Reviews() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const { data: reviews = [], isLoading } = useQuery({
    queryKey: ["reviews-mine"],
    queryFn: () => listMyReviews(true),
  });

  const decisionMutation = useMutation({
    mutationFn: ({ id, result }: { id: string; result: "approved" | "rejected" }) =>
      decideReview(id, result),
    onSuccess: () => {
      message.success("已送出審核結果");
      queryClient.invalidateQueries({ queryKey: ["reviews-mine"] });
    },
    onError: () => message.error("操作失敗，這筆審核可能已被處理"),
  });

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Typography.Title level={3} style={{ marginBottom: 4 }}>
          待我審核
        </Typography.Title>
        <Typography.Text type="secondary">指定給你的送審項目，核准後會自動打包並可下載。</Typography.Text>
      </div>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={reviews}
        pagination={false}
        locale={{ emptyText: "目前沒有待審項目" }}
        columns={[
          {
            title: "版本",
            dataIndex: "agent_slug",
            render: (slug: string) => {
              const agentSlug = slug.replace(/-v\d+$/, "");
              return <Link to={`/agents/${agentSlug}/versions/${slug}`}>{slug}</Link>;
            },
          },
          { title: "優先度", dataIndex: "priority" },
          {
            title: "送審時間",
            dataIndex: "created_at",
            render: (v: string) => new Date(v).toLocaleString(),
          },
          {
            title: "",
            key: "actions",
            render: (_: unknown, record: Review) => (
              <Space>
                <Button
                  type="primary"
                  size="small"
                  loading={decisionMutation.isPending}
                  onClick={() => decisionMutation.mutate({ id: record.id, result: "approved" })}
                >
                  核准
                </Button>
                <Button
                  danger
                  size="small"
                  loading={decisionMutation.isPending}
                  onClick={() => decisionMutation.mutate({ id: record.id, result: "rejected" })}
                >
                  退回
                </Button>
              </Space>
            ),
          },
        ]}
      />
    </div>
  );
}
