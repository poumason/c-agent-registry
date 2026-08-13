import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Form, Input, Select } from "antd";
import { useTranslation } from "react-i18next";

// Shared icon/category/hello_msg/example_questions fields for the New Agent and Edit
// Agent forms — must be rendered inside a <Form> using these exact field names
// (icon_path/category/hello_msg/example_questions), it has no Form of its own.
export default function AgentFormFields() {
  const { t } = useTranslation();

  return (
    <>
      <Form.Item label={t("myAgents.iconLabel")} name="icon_path" extra={t("myAgents.iconExtra")}>
        <Input placeholder="https://cdn.example.com/icon.png" />
      </Form.Item>
      <Form.Item label={t("common.category")} name="category">
        <Select mode="tags" placeholder="tool" tokenSeparators={[","]} />
      </Form.Item>
      <Form.Item label={t("myAgents.helloMsgLabel")} name="hello_msg">
        <Input.TextArea rows={2} placeholder={t("myAgents.helloMsgPlaceholder")} />
      </Form.Item>
      <Form.Item label={t("myAgents.exampleQuestionsLabel")}>
        <Form.List name="example_questions">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...rest }) => (
                <div key={key} style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                  <Form.Item {...rest} name={name} noStyle>
                    <Input placeholder={t("myAgents.exampleQuestionPlaceholder")} />
                  </Form.Item>
                  <Button
                    type="text"
                    icon={<MinusCircleOutlined />}
                    onClick={() => remove(name)}
                    aria-label={t("common.remove")}
                  />
                </div>
              ))}
              <Button type="dashed" icon={<PlusOutlined />} onClick={() => add()} block>
                {t("myAgents.addExampleQuestion")}
              </Button>
            </>
          )}
        </Form.List>
      </Form.Item>
    </>
  );
}
