# 验收

## 程序与财务不变量

```bash
python -m unittest discover -s tests -v
python scripts/review.py build --input examples/demo.json --out build/demo
python scripts/review.py verify --out build/demo
python scripts/make_fixture.py --out build/fixture
python scripts/review.py inspect --workbook build/fixture/source.xlsx --out build/fixture/inspection.json
python scripts/review.py extract --workbook build/fixture/source.xlsx --mapping examples/mapping.json --out build/fixture/input.json
python scripts/review.py build --input build/fixture/input.json --out build/from-excel
```

测试应覆盖净增守恒、渠道守恒、零分母、负分销、非同长周期、目标截止日、别名对账、缺失公式缓存、异常历史计数、HTML/CSV 公式注入、文件哈希。所有实际数据都须独立核对底表汇总，不能把重新加总的值当作外部核验。

comparison.xlsx 保留分销、增减、增长率与比值公式；Excel / WPS 打开时重算。Python 不计算 Excel 缓存，预计算值见 CSV 和 HTML。不得宣称已验证 Excel 渲染或重算，除非确实做过。

## 浏览器实际操作

- 2368 × 1139 和 1920 × 1080：主区域填满除导航外空间，图表不拥挤，右侧不留大块固定空白。
- 390 × 844：页面无整体横向溢出；导航、筛选、账号侧栏、讲解浮层可用。
- 逐个导航打开，确认所有图有画布、标题单位可读，无残留旧日期 / 账号 / 金额。
- 切换剔除头部：KPI、业务和渠道图更新，范围说明一致。
- 点图表账号：侧栏和高亮一致；关闭与换历史页清除焦点。
- 搜索、代理商、变化类型、排序、指标组组合使用；空结果显示 0 条，CSV 与筛选一致。
- 详情选择器改变后两图一致，联动侧栏不残留旧账号。
- 五步讲解前进后退，方向键、Esc、恢复原主题 / 范围。
- 关闭动效后数值为最终值；减少动态效果模式下可用。
- 目标数据缺失或历史数据缺失时展示明确说明，无空造数据。
- 打印只包含当前主题，侧栏 / 控件不遮挡内容。

浏览器工具必须遵守环境授权。若某工具禁止本地 file://，可正常通过仅绑定 127.0.0.1 的 HTTP 服务预览；不要绕过浏览器限制或另开未经允许的自动化后门。

validation.json 的 browser_verified 默认 false，因为生成程序无法替你做视觉检查。实际检查结论单独写 QA 记录，附真实尺寸、操作和局限，不将静态检查当浏览器实测。
