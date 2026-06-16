# Design

## Overview

产品界面服务交易复核任务，采用克制的浅色工作台风格。页面应优先支持扫描、比较和重复查看，不使用营销式 hero、装饰性动效或高饱和大面积背景。

## Color

现有色彩以 `app.css` tokens 为准：浅灰背景、白色 surface、青绿色 accent、深色 ink、语义化 success/warning/danger/critical/info/neutral。状态色只用于风险徽标、数值正负、当前导航和关键提醒，不做装饰性铺色。

## Typography

使用系统 sans 字体栈：`Inter`, `Segoe UI`, `Microsoft YaHei`, `PingFang SC`, `Arial`, `sans-serif`。产品 UI 使用固定 rem 字号和断点，不使用流式标题字号。标题服务页面识别，数据标签和表格文本保持紧凑可读。

## Layout

页面使用顶栏导航、页面标题、指标卡、工作区卡和明细表格。首页指标卡只展示状态，工作区卡承担入口。详情页使用 page heading + metric grid + section card 的稳定结构。

## Components

- `risk-badge` 表达低/中/高/严重、信息和中性状态。
- `data-freshness` 表达数据新鲜度，每个模块显示自己的数据时点。
- `card-link` 只用于明确入口，不在指标卡和工作区卡重复出现同一 CTA。
- `data-table` 用于高密度明细，移动端固定 `identity-cell` 标的列，避免横向滚动时丢失代码/名称上下文。
- `empty-state` 必须说明缺什么、为什么缺、下一步去哪里。

## Interaction

主导航使用 `aria-current="page"` 标识当前页面。表格横向滚动容器可聚焦。移动触控目标最小 44px。动效仅限 hover/active 状态反馈，不使用页面加载编排。

## Copy

文案应明确数据来源和限制。样本不足、数据不完整、外部数据降级时直接说明原因，不使用模糊的 `N/A` 或 `暂无详情` 作为核心模块终点。
