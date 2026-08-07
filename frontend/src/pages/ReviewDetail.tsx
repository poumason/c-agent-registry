import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App,
  Breadcrumb,
  Button,
  Card,
  Descriptions,
  Empty,
  Form,
  Input,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";
import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { decideReview, getReview } from "../api/reviews";
import { listMcps, listSkills } from "../api/skills";
import { getVersion, listDependencies } from "../api/versions";
import { ReviewResultTag, VersionStatusTag } from "../components/tags";

export default function ReviewDetail() {
  const { message } = App.useApp();
  const { reviewId } = useParams<{ reviewId: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<{ comment?: string }>();

  const reviewQuery = useQuery({
    queryKey: ["review", reviewId],
    queryFn: () => getReview(reviewId!),
    enabled: !!reviewId,
  });

  const versionSlug = reviewQuery.data?.agent_slug;
  const agentSlug = versionSlug?.replace(/-v\d+$/, "");

  const versionQuery = useQuery({
    queryKey: ["version", versionSlug],
    queryFn: () => getVersion(versionSlug!),
    enabled: !!versionSlug,
  });
  const depsQuery = useQuery({
    queryKey: ["version-deps", versionSlug],
    queryFn: () => listDependencies(versionSlug!),
    enabled: !!versionSlug,
  });
  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: listSkills });
  const mcpsQuery = useQuery({ queryKey: ["mcps"], queryFn: listMcps });

  const skillNameById = useMemo(
    () => new Map((skillsQuery.data ?? []).map((s) => [s.id, `${s.name} v${s.version}`])),
    [skillsQuery.data],
  );
  const mcpNameById = useMemo(
    () => new Map((mcpsQuery.data ?? []).map((m) => [m.id, `${m.name} v${m.version}`])),
    [mcpsQuery.data],
  );

  const decisionMutation = useMutation({
    mutationFn: ({ result, comment }: { result: "approved" | "rejected"; comment?: string }) =>
      decideReview(reviewId!, result, comment),
    onSuccess: () => {
      message.success("已送出審核結果");
      queryClient.invalidateQueries({ queryKey: ["review", reviewId] });
      queryClient.invalidateQueries({ queryKey: ["reviews-mine"] });
      if (versionSlug) {
        queryClient.invalidateQueries({ queryKey: ["version", versionSlug] });
        queryClient.invalidateQueries({ queryKey: ["version-reviews", versionSlug] });
      }
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(msg ?? "操作失敗，這筆審核可能已被處理");
    },
  });

  if (reviewQuery.isLoading || !reviewQuery.data) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  const review = reviewQuery.data;
  const version = versionQuery.data;
  const isPending = review.result === "pending";
  const isMyReview = user?.id === review.reviewer_id;
  const canDecide = isPending && (isMyReview || user?.role === "admin");

  const submit = (result: "approved" | "rejected") => {
    const comment = (form.getFieldValue("comment") as string | undefined)?.trim();
    if (result === "rejected" && !comment) {
      form.setFields([{ name: "comment", errors: ["退回時必須填寫原因，讓提交者知道要改什麼"] }]);
      return;
    }
    decisionMutation.mutate({ result, comment: comment || undefined });
  };

  return (
    <div>
      <Breadcrumb
        items={[{ title: <Link to="/reviews">待我審核</Link> }, { title: versionSlug ?? "…" }]}
        style={{ marginBottom: 8, fontSize: 12.5 }}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <Typography.Title level={3} style={{ marginBottom: 0 }}>
          審核：{versionSlug}
        </Typography.Title>
        <ReviewResultTag result={review.result} />
      </div>

      <Card title="版本內容" size="small" style={{ marginBottom: 18 }}>
        {version ? (
          <>
            <Descriptions column={1} size="small" style={{ marginBottom: 12 }}>
              <Descriptions.Item label="狀態">
                <VersionStatusTag status={version.status} />
              </Descriptions.Item>
              <Descriptions.Item label="Endpoint URL">
                {version.url ?? <Typography.Text type="secondary">（無）</Typography.Text>}
              </Descriptions.Item>
              <Descriptions.Item label="Streaming">{version.streaming ? "是" : "否"}</Descriptions.Item>
              <Descriptions.Item label="Input Modes">
                {version.default_input_modes.length ? (
                  <Space wrap>
                    {version.default_input_modes.map((m) => (
                      <Tag key={m}>{m}</Tag>
                    ))}
                  </Space>
                ) : (
                  <Typography.Text type="secondary">（無）</Typography.Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Output Modes">
                {version.default_output_modes.length ? (
                  <Space wrap>
                    {version.default_output_modes.map((m) => (
                      <Tag key={m}>{m}</Tag>
                    ))}
                  </Space>
                ) : (
                  <Typography.Text type="secondary">（無）</Typography.Text>
                )}
              </Descriptions.Item>
            </Descriptions>

            <div style={{ fontSize: 11.5, fontWeight: 600, color: "#9AA0AC", marginBottom: 8 }}>
              依賴的 SKILL / MCP
            </div>
            {depsQuery.data && depsQuery.data.length > 0 ? (
              <Space wrap style={{ marginBottom: 12 }}>
                {depsQuery.data.map((d) => {
                  const label =
                    d.type === "skill"
                      ? skillNameById.get(d.dependency_id) ?? d.dependency_id
                      : mcpNameById.get(d.dependency_id) ?? d.dependency_id;
                  return (
                    <Tag key={d.id} color={d.type === "mcp" ? "geekblue" : "default"}>
                      {label} <span style={{ opacity: 0.6 }}>{d.type}</span>
                    </Tag>
                  );
                })}
              </Space>
            ) : (
              <Empty
                description="尚未加入任何依賴"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                style={{ margin: "8px 0 12px" }}
              />
            )}

            <Link to={`/agents/${agentSlug}/versions/${versionSlug}`}>在 Agent 詳情頁查看 →</Link>
          </>
        ) : (
          <Spin />
        )}
      </Card>

      <Card title="審核意見" size="small">
        {canDecide ? (
          <Form form={form} layout="vertical">
            <Form.Item
              label="Comment"
              name="comment"
              extra="退回時必須填寫原因；核准則為選填。"
            >
              <Input.TextArea rows={4} placeholder="給提交者的意見…" />
            </Form.Item>
            <Space>
              <Button
                type="primary"
                loading={decisionMutation.isPending}
                onClick={() => submit("approved")}
              >
                核准
              </Button>
              <Button danger loading={decisionMutation.isPending} onClick={() => submit("rejected")}>
                退回
              </Button>
            </Space>
          </Form>
        ) : isPending ? (
          <Typography.Text type="secondary">這不是指派給你的審核項目，無法操作。</Typography.Text>
        ) : (
          <div>
            <div style={{ marginBottom: review.comment ? 10 : 0 }}>
              結果：<ReviewResultTag result={review.result} />
            </div>
            {review.comment && (
              <Typography.Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                {review.comment}
              </Typography.Paragraph>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
