# 稻田经营复盘 · Agent Skill

从经营 Excel 生成可核验的分销 / 自营重算表和稻田品牌交互报告。公司原始 AI Logo 和渲染 PNG 随技能保留；示例为独立构造的模拟数据。

**同一套计算、组件和验收，降低切换模型后的差异。** 不是一段“画漂亮报表”的提示词，也不承诺任意模型的业务判断完全相同。

## 直接使用

```bash
gh repo clone stonele01/daotian-business-review
cd daotian-business-review
```

需要 Python 3.10+，不需要 Node、前端构建、模型 API 或在线图表服务。

```bash
python -m pip install -r requirements.txt
python scripts/review.py build --input examples/demo.json --out build/demo
python scripts/review.py verify --out build/demo
```

打开 `build/demo/report.html`。如浏览器环境限制 file://，可使用：

```bash
python -m http.server 8772 --bind 127.0.0.1 --directory build/demo
```

然后访问 `http://127.0.0.1:8772/report.html`。

## 安装为个人技能

```bash
python scripts/install.py
```

默认安装到 `$CODEX_HOME/skills/daotian-business-review`，未设置 CODEX_HOME 时使用 `~/.codex/skills/daotian-business-review`。已有不同版本时先检查差异，再用 `--update`。其他支持 Agent Skills 的宿主可把整个技能目录放进其技能发现目录，或使用 `--dest /path/to/skills/daotian-business-review`；不要只复制 SKILL.md。

重新加载技能后，示例指令：

> 使用 $daotian-business-review 分析这份 Excel。本期和上期以我确认的日期为准，保留公司 Logo，输出重算表和可交互复盘报告，不做库存预警。

也可以补充“只根据数据分析”或“结合已授权会议内容，分开数据事实与会议陈述”。

## 输入与交付

1. `inspect` 读取 Excel 单元格、公式和缓存。
2. Agent 确认日期、单位、账号范围和目标口径，依据 [映射规范](references/workbook-mapping.md) 建立映射。
3. `extract` 对齐账号、检查别名和渠道总额，输出 [规范化 JSON](references/data-contract.md)。
4. `build` 用固定程序计算与生成；`verify` 核验产物与哈希。
5. 按 [验收清单](references/acceptance.md) 实际查看宽屏、窄屏和交互。

| 交付 | 内容 |
|---|---|
| report.html | 单文件离线交互报告，内嵌 Logo、数据、ECharts 和样式 |
| comparison.xlsx | 分销、自营、消耗、增减与比值；保留公式，Excel / WPS 打开时重算 |
| comparison.csv | 以元为单位的预计算明细，可直接检查 |
| analysis.json | 以整数分为货币单位的完整计算结果 |
| validation.json | 输入及产物哈希、对账结果、异常与浏览器验证边界 |

## 已固化的能力

- 全盘 KPI、净增瀑布、动态头部剔除、CR1/CR3。
- 账号贡献、渠道拆分、规模 / 增长散点、账号 × 渠道热图。
- 自营 / 消耗、对称算术分解、前后比值哑铃、代理商汇总。
- 同口径目标对比、剩余差额和确认 MTD 后的目标日均。
- 账号搜索、筛选、排序、指标切换、CSV 导出、图表联动侧栏。
- 独立历史周期、逐指标条形与明细、异常计数隔离。
- 五步讲解、数值与图表动效、减少动态效果、功能指南、当前主题打印。
- 全宽桌面、手机适配、ResizeObserver；保留真实品牌资产。

没有对应数据时不生成逐日趋势、商品爆款、利润或库存预警；不将算术拆分写成因果归因。

## 开发与验证

```bash
python -m unittest discover -s tests -v
python scripts/make_fixture.py --out build/fixture
python scripts/review.py extract --workbook build/fixture/source.xlsx --mapping examples/mapping.json --out build/fixture/input.json
python scripts/review.py build --input build/fixture/input.json --out build/from-excel
```

测试涵盖财务守恒、零分母、负值、渠道和汇总对账、公式缓存缺失、别名冲突、历史隔离、输出转义和源文件不变。浏览器验收记录见 [QA.md](QA.md)。

技能按 [Agent Skills 标准](https://agentskills.io/specification) 和 [技能编写最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) 组织：短入口、按需参考文档、固定脚本、独立模拟样例与回归测试。跨模型能力边界见 [portability.md](references/portability.md)。

仓库不包含原始经营工作簿、会议正文、真实分析结果或身份凭据。生成物和私人输入由 .gitignore 排除。第三方库说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。

原创代码与文档采用 [MIT License](LICENSE)。公司 Logo 作为品牌参考单独保留，第三方库保留各自声明。其他团队可以替换 `assets/brand/company-logo.png` 与品牌配色后使用自己的品牌版本。
