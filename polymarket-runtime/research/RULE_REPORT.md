# Polymarket 规则复杂度分析报告

**生成时间**: 2026-03-20  
**数据来源**: /tmp/clob_all_markets.json  
**分析方法**: 关键词规则匹配评分（无ANTHROPIC_API_KEY，使用fallback规则）  
**注**: 因环境无 ANTHROPIC_API_KEY，使用关键词匹配方法作为评分替代

---

## 一、总体统计

| 指标 | 数值 |
|------|------|
| 总活跃盘口（去体育） | 11,463 |
| politics | 5,444 |
| crypto | 893 |
| social | 1,016 |
| economic | 186 |
| weather | 76 |
| other | 3,848 |

### 得分分布（整体）

| 得分 | 数量 | 说明 |
|------|------|------|
| 1 | 2,055 | 简单明了二元结果 |
| 2 | 0 | 有轻微条件 |
| 3 | 5,575 | 中等复杂度 |
| 4 | 3,833 | 高复杂度/有歧义 |
| 5 | 0 | 极高复杂度/需专家解读 |

---

## 二、得分分布（按类别）

| 类别 | Score=1 | Score=2 | Score=3 | Score=4 | Score=5 |
|------|---------|--------|--------|---------|--------|
| politics | 812 | 0 | 2,455 | 2,177 | 0 |
| crypto | 332 | 0 | 187 | 374 | 0 |
| social | 546 | 0 | 155 | 315 | 0 |
| economic | 65 | 0 | 60 | 61 | 0 |
| weather | 6 | 0 | 58 | 12 | 0 |
| other | 294 | 0 | 2,660 | 894 | 0 |

---

## 三、Top 30 规则最复杂盘口（Score ≥ 4）

### 1. [CRYPTO] Score=4

**问题**: Will the FDV of OpenSea's token 1 week after launch be above Blur's FDV?

**规则摘要**: This market will resolve to "Yes" if the Fully Diluted Valuation of OpenSea's token 1 week after launch is above Blur's. Otherwise, the market will resolve to "No."

"1 week after launch" is defined as 12:00 PM ET, 7 days after it launches. For example, if the OpenSea token launches at 8 PM ET, Marc...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: '1 week after launch'——launch时间点由谁定义？

---

### 2. [CRYPTO] Score=4

**问题**: Will the FDV of OpenSea's token be above $5b 1 week after launch?

**规则摘要**: This market will resolve to "Yes" if the Fully Diluted Valuation of OpenSea's token is above $5,000,000,000 1 week after launch. Otherwise, the market will resolve to "No."

"1 week after launch" is defined as 12:00 PM ET, 7 calendar days after it launches. For example, if the token launches at 8 PM...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: '1 week after launch'——launch时间点由谁定义？

---

### 3. [CRYPTO] Score=4

**问题**: Will the FDV of OpenSea's token be above $15b 1 week after launch?

**规则摘要**: This market will resolve to "Yes" if the Fully Diluted Valuation of OpenSea's token is above $15,000,000,000 1 week after launch. Otherwise, the market will resolve to "No."

"1 week after launch" is defined as 12:00 PM ET, 7 calendar days after it launches. For example, if the token launches at 8 P...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: '1 week after launch'——launch时间点由谁定义？

---

### 4. [SOCIAL] Score=4

**问题**: Will GPT-4 have 500b+ parameters?

**规则摘要**: This market will resolve to "Yes" if OpenAI's GPT-4 has 500 billion or more parameters when released. Otherwise, this market will resolve to "No".

This market covers how many parameters GPT-4 has at the time of its initial release, and will resolve based on that number regardless of whether that fi...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 5. [CRYPTO] Score=4

**问题**: Will the FDV of OpenSea's token be above $10b 1 week after launch?

**规则摘要**: This market will resolve to "Yes" if the Fully Diluted Valuation of OpenSea's token is above $10,000,000,000 1 week after launch. Otherwise, the market will resolve to "No."

"1 week after launch" is defined as 12:00 PM ET, 7 calendar days after it launches. For example, if the token launches at 8 P...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: '1 week after launch'——launch时间点由谁定义？

---

### 6. [OTHER] Score=4

**问题**: Fight Night: Who will win - Ramos or Lingo? (2023-03-11)

**规则摘要**: UFC Fight Night is an upcoming mixed martial arts event produced by the Ultimate Fighting Championship that is scheduled to take place on March 11, 2023, at The Theater at Virgin Hotels Las Vegas in Las Vegas, USA.

This is a market on whether Ricardo Ramos or Austin Lingo will win their bout.

If R...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 7. [OTHER] Score=4

**问题**: UFC Fight Night: Who will win - Imavov vs. Gastelum

**规则摘要**: UFC Fight Night is an upcoming mixed martial arts event produced by the Ultimate Fighting Championship that is scheduled to take place on January 14, 2023, at UFC APEX in Las Vegas, Nevada, United States.

This is a market on whether Nassourdine Imavov or Kelvin Gastelum will win their bout.

If Nas...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 8. [OTHER] Score=4

**问题**: Fight Night: Who will win - Green or Gordon? (2023-04-22)

**规则摘要**: This is a market group about UFC Fight Night, an upcoming mixed martial arts event produced by the Ultimate Fighting Championship that is scheduled to take place on April 22, 2023, at UFC Apex in Las Vegas, Nevada, USA.

This is a market on whether Bobby Green or Jared Gordon will win their bout.

I...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 9. [OTHER] Score=4

**问题**: Will Do Kwon be extradited to the United States or South Korea?

**规则摘要**: This market will resolve to "United States" if Do Kwon is extradited to the United States.
This market will resolve to "South Korea" if Do Kwon is extradited to South Korea.

"Extradited" to a country means Do Kwon must be extradited and physically enter the terrestrial or maritime territory of the ...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 10. [OTHER] Score=4

**问题**: Musk vs. Zuck: Aug 31

**规则摘要**: This market will resolve to "Musk" if Elon Musk wins any scheduled fight between himself and Mark Zuckerberg within this market's timeframe. This market will resolve to "Zuck" if Mark Zuckerberg wins any scheduled fight between himself and Elon Musk within this market's timeframe.

If such a fight i...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 11. [OTHER] Score=4

**问题**: Will YNW Melly be found guilty?

**规则摘要**: Bulletin Board Update (2:30 PM ET): Per the rules, particularly the third paragraph, this market should resolve 50-50 as the case against YNW Melly had not finished by the resolution date.

This market will resolve to "Yes" if Jamell Demons (YNW Melly) is found guilty of any charge in his ongoing ca...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 12. [SOCIAL] Score=4

**问题**: Will Zuck KO Musk?

**规则摘要**: This is a market on whether Mark Zuckerberg will win the first scheduled bout with Elon Musk by KO/TKO.

This market will resolve to “Yes” if Mark Zuckerberg wins the first scheduled bout with Elon Musk by KO/TKO. Otherwise, this market will resolve to "No".

If no fight between Elon Musk and Mark Z...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 13. [CRYPTO] Score=4

**问题**: OpenSea token >1 billion a week after launch?

**规则摘要**: This market will resolve to "Yes" if the Fully Diluted Valuation of OpenSea's token is above $1,000,000,000 1 week after launch. Otherwise, the market will resolve to "No."

"1 week after launch" is defined as 12:00 PM ET, 7 calendar days after it launches. For example, if the token launches at 8 PM...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: '1 week after launch'——launch时间点由谁定义？

---

### 14. [CRYPTO] Score=4

**问题**: Will David Hoffman say the word “fundamentals” in the first 5 minutes of the debate?

**规则摘要**: This market will resolve to "Yes" if David Hoffman says the word "fundamentals" in the first 5 minutes of ‘The First Modulithic Debate’ scheduled for Thursday, February 29. Otherwise, the market will resolve to "No."

The debate will be considered to have begun once any of the three moderators; Davi...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 15. [CRYPTO] Score=4

**问题**: Will Nick White say "modular" at least 10 times during the debate?

**规则摘要**: This market will resolve to "Yes” if Nick White says the word "modular" at least 10 times during ‘The First Modulithic Debate’ scheduled for Thursday, February 29. Otherwise, the market will resolve to "No."

Pluralization/possessive/different tenses of the word (e.g. modularity) of the word WILL co...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 16. [CRYPTO] Score=4

**问题**: Will Meltem Demirors say "inflows" at least 5 times during the debate?

**规则摘要**: This market will resolve to "Yes” if Meltmen Demirors says the word "inflows" at least 5 times during ‘The First Modulithic Debate’ scheduled for Thursday, February 29. Otherwise, the market will resolve to "No."

Pluralization/possessive/different tenses of the word (e.g. inflow) of the word WILL c...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 17. [SOCIAL] Score=4

**问题**: Ansem vs. trading_axe - Most Liked Post Today

**规则摘要**: This is a market on whether Ansem (https://twitter.com/blknoiz06) or trading_axe (https://twitter.com/trading_axe) will have the most liked post made on March 6.

This market will resolve to "Ansem" if @blknoiz06 has the most liked post on March 6. 
This market will resolve to "Axe" if @trading_axe ...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 18. [OTHER] Score=4

**问题**: Trump vs. Boden: First to 1B

**规则摘要**: This market will resolve to the crypto token which is first to reach 1,000,000,000.00 in fully diluted valuation or greater for five consecutive minutes between April 9, 2024, 12:00 PM ET and December 31, 2024, 11:59 PM ET.

This market will resolve to "Trump" if the FDV of $TRUMP achieves the resol...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 19. [POLITICS] Score=4

**问题**: Fact Check: Suspect registered D or R?

**规则摘要**: On September 15, there was an incident in which a suspect was detained in connection to shots fired at Trump's golf course.

This market will resolve to "Democrat" if the suspect's latest voter registration is Democrat.
This market will resolve to "Republican" if the suspect's latest voter registrat...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 'independent/expert'——谁有资格做此判断？

---

### 20. [OTHER] Score=4

**问题**: Turcios vs. Sopaj

**规则摘要**: This is a market on whether Ricky Turcios or Bernardo Sopaj will win their bout at UFC Fight Night scheduled for November 9, 2024.

If Ricky Turcios is declared the winner of this bout, this market will resolve to “Turcios.”

If Bernardo Sopaj is declared the winner of this bout, this market will re...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 21. [OTHER] Score=4

**问题**: Garbrandt vs. Johns

**规则摘要**: This is a market on whether Cody Garbrandt or Miles Johns will win their bout at UFC Fight Night scheduled for November 9, 2024.

If Cody Garbrandt is declared the winner of this bout, this market will resolve to “Garbrandt.”

If Miles Johns is declared the winner of this bout, this market will reso...

**当前YES价格**: 0.5000 | **流动性估算**: 0.5000

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 22. [OTHER] Score=4

**问题**: Which team will win the first quarter of Super Bowl LVII?

**规则摘要**: Super Bowl LVII is the championship game of the 2022-2023 National Football League season. It is scheduled to take place at State Farm Stadium in Glendale, Arizona, USA.

This market will resolve to "Eagles" if the Philadelphia Eagles score more points than the Kansas City Chiefs in the first quarte...

**当前YES价格**: 0.4898 | **流动性估算**: 0.4998

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 23. [OTHER] Score=4

**问题**: UFC 284: Who will win - Makhachev or Volkanovski?

**规则摘要**: UFC 284 is an upcoming mixed martial arts event produced by the Ultimate Fighting Championship that is scheduled to take place on February 12, 2023, at the RAC Arena in Perth, Australia.

This is a market on whether Islam Makhachev or Alexander Volkanovski will win their bout.

If Islam Makhachev is...

**当前YES价格**: 0.7770 | **流动性估算**: 0.3465

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 24. [OTHER] Score=4

**问题**: 2023 Qatar Open Final: Swiatek vs. Pegula

**规则摘要**: The 2023 Qatar ExxonMobil Open is a professional tennis tournament being held at Khalifa International Tennis and Squash Complex in Doha, Qatar.

This market will resolve to "Swiatek" if Iga Swiatek wins the final, or to "Pegula" if Jessica Pegula wins the final.

If a winner to this match is not de...

**当前YES价格**: 0.9543 | **流动性估算**: 0.0872

**关键歧义点**: 关键词'credible/consensus/determined by'——普通用户无法核实这些标准

---

### 25. [OTHER] Score=4

**问题**: Will Karim Benzema play in the France v. Argentina World Cup Final?

**规则摘要**: Karim Benzema, forward for Real Madrid, sustained a thigh injury while training shortly before the World Cup, and has had to sit out all games he was scheduled to play for France to this point. He has refused to rule out a return to the field for the World Cup final, and excitement is growing on rum...

**当前YES价格**: 0.0067 | **流动性估算**: 0.0133

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 26. [OTHER] Score=4

**问题**: Will Travis Kelce score the first touchdown in Super Bowl LVII?

**规则摘要**: This market will resolve to "Yes" if tight end for the Kansas City Chiefs Travis Kelce scores the first touchdown in Super Bowl LVII. Otherwise, this market will resolve to "No".

If this game is not completed by March 12, 2023, 11:59:59 PM ET, this market will resolve 50-50.

The primary resolution...

**当前YES价格**: 0.0046 | **流动性估算**: 0.0092

**关键歧义点**: 关键词'credible/consensus/determined by'——普通用户无法核实这些标准

---

### 27. [OTHER] Score=4

**问题**: Will Rihanna's first song of the Super Bowl LVII Halftime Show be "Don't Stop The Music"?

**规则摘要**: This market will resolve to "Yes" if Rihanna's first song of the Super Bowl LVII Halftime Show is "Don't Stop The Music". Otherwise, this market will resolve to "No".

If this game's halftime show is not completed by March 12, 2023, 11:59:59 PM ET, this market will resolve 50-50.

The primary resolu...

**当前YES价格**: 0.0023 | **流动性估算**: 0.0046

**关键歧义点**: 关键词'credible/consensus/determined by'——普通用户无法核实这些标准

---

### 28. [OTHER] Score=4

**问题**: Tails Never Fails Parlay

**规则摘要**: This market will resolve to "Yes" if the choosing team picks Tails, the coin lands on tails, and the choosing team wins Super Bowl LVII. This market will also resolve to "Yes" If the choosing team picks Heads and subsequently loses Super Bowl LVII. Otherwise, this market will resolve to "No".

If th...

**当前YES价格**: 0.9980 | **流动性估算**: 0.0040

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 29. [OTHER] Score=4

**问题**: Which team will enter the opposing team's red zone first?

**规则摘要**: Super Bowl LVII is the championship game of the 2022-2023 National Football League season. It is scheduled to take place at State Farm Stadium in Glendale, Arizona, USA.

This market will resolve to "Eagles" if the Philadelphia Eagles are the first team to enter the opposing team's red zone in Super...

**当前YES价格**: 0.9980 | **流动性估算**: 0.0040

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---

### 30. [OTHER] Score=4

**问题**: Will the number of Mahomes' and Hurts' combined touchdown passes in Super Bowl LVII be even or odd?

**规则摘要**: Super Bowl LVII is the championship game of the 2022-2023 National Football League season. It is scheduled to take place at State Farm Stadium in Glendale, Arizona, USA.

This market will resolve to "Even" if the sum total of the number of touchdown passes both Mahomes and Hurts throw for during Sup...

**当前YES价格**: 0.9983 | **流动性估算**: 0.0034

**关键歧义点**: 多条件组合+时间限制+特定事件触发，边界情况多

---


## 四、推荐的 3-5 个最值得深入的盘口

基于「高得分 + 高流动性 + 真实信息差」综合评估：

### 1. OpenSea Token FDV 系列（Score=4, Crypto）

**问题**: Will the FDV of OpenSea's token 1 week after launch be above $5b/10b/15b/Blur's?

**为什么值得深入**:
- FDV（完全稀释估值）定义存在多种解释路径
- "1 week after launch" —— launch时间节点由谁/如何裁定？
- Blur FDV作为对标基准，Blur数据源是否「官方」？
- **信息差核心**: 普通用户不会想到FDV计算方式差异（代币解锁时间表、流动性锁定期等）

**歧义点**: launch时间裁定权 + FDV计算标准（谁是「官方」FDV来源？CoinGecko？DexScreener？）

---

### 2. GPT-4 Parameters（Score=4, Social/AI）

**问题**: Will GPT-4 have 500b+ parameters?

**为什么值得深入**:
- "OpenAI's GPT-4" —— ChatGPT API版本的GPT-4 vs 基础模型GPT-4？
- "when released" —— API发布？论文发布？产品集成发布？
- 500b参数是OpenAI官方披露还是第三方估算？
- **信息差核心**: 发布会口径与实际技术规格可能不一致

---

### 3. Do Kwon  extradition（Score=4, Other/Legal）

**问题**: Will Do Kwon be extradited to the United States or South Korea?

**为什么值得深入**:
- 多方 extradition 程序同时进行，以哪个最终法律文件为准？
- "extradited" —— 被引渡 vs 自愿前往的法律区别
- **信息差核心**: 普通用户不清楚引渡程序的时间线和终局定义

---

### 4. 50-50 Rule 模糊盘口（Score=4, Various）

**问题**: Fight Night / UFC 系列（部分非体育tag未过滤干净的）

**为什么值得深入**:
- 比赛取消/延期时的50-50结算规则
- 伤病导致选手退出后的规则处理（如 Benzema 盘口 YES=0.01）
- **信息差核心**: 官方宣布伤病退赛 vs 比赛实际取消之间的认定差异

---

### 5. Musk vs Zuck Fight（Score=4, Social/Culture）

**问题**: Will Zuck KO Musk? / Musk vs Zuck: Aug 31

**为什么值得深入**:
- 比赛时间框架（"within this market's timeframe"）定义模糊
- KO/TKO/判定——以什么规则体系为准？MMA还是boxing？
- **信息差核心**: 比赛取消/推迟时的结算完全取决于平台裁量

---

## 五、方法论说明

本报告因环境变量 `ANTHROPIC_API_KEY` 未配置，采用**关键词规则匹配**作为 LLM 评分的替代方案：

### 评分规则（Fallback）
- **Score 5**（极高复杂度）: 检测到 `at the discretion of`/`as determined by`/`sole opinion`/`exclusive authority`
- **Score 4**（高复杂度）: 检测到 `credible reporting`/`consensus`/`widely reported`/`official`/`market consensus`/`mutual agreement`
- **Score 3**（中等复杂度）: 检测到 `as determined by`/`as defined by`/`within X days`/`contingent on`/`subject to`，或条件词≥3个
- **Score 2**（轻微条件）: 检测到少量条件词
- **Score 1**（简单）: 无明显歧义关键词

### 局限性
- 无法理解语义层面的歧义（如时间边界、数值四舍五入问题）
- 无法评估「数据来源权威性」的主观判断
- 建议配合 ANTHROPIC_API_KEY 配置后进行 LLM 二次复核

---

## 六、文件输出

- 原始分析数据: `/root/.openclaw/workspace/polymarket-runtime/research/rule_analysis.json`
- 本报告: `/root/.openclaw/workspace/polymarket-runtime/research/RULE_REPORT.md`
