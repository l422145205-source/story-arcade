# 看一眼，还是拆开看？

全部为原创虚构案例，产物来自真实执行的 Python CLI；示例路径是预设的脚本化选择，不是独立 Agent 评测，也不是真实玩家记录。

## 开局与半途停下（含少量线索）

- [乘客开局](demo/opening.md) / [JSON](demo/opening.json)
- [录音志愿者开局](demo/volunteer-opening.md) / [JSON](demo/volunteer-opening.json)：同一事件，初始知识不同。
- [做出两次选择之后](demo/checkpoint.md) / [JSON](demo/checkpoint.json)：尚未解锁最终结论。
- [接力包](demo/relay/relay.md) / [存档](demo/relay/relay.save.json)：接收方使用相同故事版本继续这一视角。

## 作者与结局（剧透）

<details>
<summary>我想看完整分支和验证结果</summary>

- [私下核验路线](demo/quiet-ending.md) / [JSON](demo/quiet-ending.json)
- [公开传播路线](demo/public-ending.md) / [JSON](demo/public-ending.json)
- [便利店短局](demo/shop-ending.md) / [JSON](demo/shop-ending.json)
- [作者侧状态探索](demo/author-audit.json)：列出三个起始视角的已探索状态及结局路径；只代表这些小型作者规则图。
- [重试、接力与分支检查](demo/verification.json)
- [逐步工具视图](demo/frames.json)：包含最后结局。

</details>

重新生成：在仓库根目录执行 `python tools/reproduce.py --out work/my-demo`（输出目录须不存在）。它实际运行 `new`、`act`、重复事件重试、`fork`、`relay` 和 `audit`，不调用模型，也不联网。

所有底层剧本文件包含作者答案，开源格式不提供防止读源码剧透的安全隔离。
