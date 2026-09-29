# 规范化输入 v1

以 `examples/demo.json` 为可执行完整样例。金额输入单位是人民币元，程序用 Decimal 四舍五入到分，后续金额求和使用整数分。输出 analysis.json 的货币单位为分；比率是小数。

| 字段 | 要求 |
|---|---|
| schema_version | 固定 1 |
| meta.title | 报告名 |
| meta.period / baseline | `{start:"YYYY-MM-DD",end:"YYYY-MM-DD"}`，日期必须明确 |
| meta.currency | CNY；其他币种先显式换算 |
| meta.source | 文件名；不要放敏感绝对路径 |
| accounts | 非空；唯一非空 name，可选 agency、source_refs |
| accounts[].total / self / spend | `{current:数值,prior:数值}`；都必填，空白不补零 |
| accounts[].channels | 可省略；提供时每个账号同顺序完整渠道，`{name,current,prior}`；每期渠道合计与总额误差 ≤ 0.01 元 |
| accounts[].target | 可选 `{amount,actual,scope}`；目标 null 或 0 时不计算完成率；actual 与 scope 必填 |
| targets | 可选独立板块目标列表 `{name,amount,actual,scope}`；不自动加总重叠板块 |
| checks | 可选独立底表合计，如 `{"total_current":10000,"self_prior":2000}`；单位元，不允许把程序结果再充作源表核验 |
| issues | 已知口径冲突 / 不使用指标及原因，字符串列表 |
| commentary | 可选事实、会议、假设、行动，见 editorial.md |

月节奏需要显式 `meta.target_context`：

```json
{"start":"2030-04-01","as_of":"2030-04-15","actual_is_month_to_date":true,"scope":"总 GMV，完整月初至截止日","amount":800000,"actual":320000}
```

该上下文独立于其他范围的 targets，不能把切片排录播的目标配上含录播 GMV。截止日必须与起始日同年月，起始日为 1 号。月底剩余天数为 0 时所需日均为空。

## 历史专题

`history` 中每组包含 title、period、baseline、metrics、rows、notes。日期不继承当前周期。

```json
{"title":"短视频","period":{"start":"2030-03-01","end":"2030-03-15"},"baseline":{"start":"2030-02-01","end":"2030-02-15"},"metrics":[{"key":"views","label":"曝光","unit":"次","integer":true},{"key":"clicks","label":"点击人数","unit":"人","integer":true},{"key":"ctr","label":"点击率","unit":"%","numerator":"clicks","denominator":"views"}],"rows":[{"name":"示例账号","values":{"views":{"current":1000,"prior":900},"clicks":{"current":60,"prior":70}}}],"notes":["人数未跨账号去重；不是同一人群跟踪漏斗。"]}
```

非比例指标需显式提供 current/prior；缺失用 null。非法计数（负数、小数）隔离并显示提示。派生指标引用前面已声明的非派生指标；单位 % 时输入值是比例，界面乘 100。金额型历史指标使用声明的单位，不自动转换。一个专题可包含 GMV、曝光、观看、点击、成交、销量、款式等，用户逐项切换并查看明细。

## 核心不变量

1. 分销 + 自营 = 总 GMV；本期 − 上期 = 增减额。
2. 正向增量 + 负向抵消 = 全盘净增量。
3. 有效正消耗时，两项对称分解合计 = 自营增减额（浮点尾差容忍 0.0001 分）。
4. 比率无有效分母时为 null；不能输出 Infinity / NaN。
5. CR1 / CR3 分别按各期排名；有负总 GMV 时不展示集中度与规模占比。
6. 目标和渠道都是独立维度，不把它们与总 GMV 再次相加。
