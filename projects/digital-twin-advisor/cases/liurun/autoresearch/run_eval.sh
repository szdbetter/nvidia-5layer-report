#!/bin/bash
# Usage: ./run_eval.sh <version_number>
# e.g., ./run_eval.sh 1

VERSION=$1
PROMPT_FILE="/root/.openclaw/workspace/projects/digital-twin-advisor/cases/liurun/autoresearch/system_prompt_v${VERSION}.md"
OUTPUT_FILE="/root/.openclaw/workspace/projects/digital-twin-advisor/cases/liurun/autoresearch/eval_results_v${VERSION}.json"

SYSTEM_PROMPT=$(cat "$PROMPT_FILE")

QUESTIONS=(
  "我的餐饮生意越来越难做，要不要关店转行做电商？"
  "员工总是执行不到位，是员工问题还是管理问题？"
  "现在AI这么热，我一个传统制造业老板，要怎么用AI？"
  "怎么判断一个新赛道值不值得进入？"
  "公司现金流很紧，但老板说要扩张，怎么办？"
  "为什么很多努力工作的人，收入反而不高？"
  "我想给团队做激励，发奖金还是涨工资哪个更有效？"
  "平台电商流量越来越贵，品牌还有出路吗？"
  "古巴的经济实验给中小企业主什么启示？"
  "一个人公司（独立顾问/自由职业）有没有天花板？"
)

EVAL_SYSTEM='你是严格的评估员，只输出JSON，不输出任何其他内容'
EVAL_RULES='根据以下5条规则对回答打分，每条yes=1 no=0，只输出JSON格式：{"scores":[1,0,1,1,1],"total":4,"fails":["规则2失败原因"]}

规则：
1. 案例引入：回答开头是否用了具体的真实故事/案例/数据切入，而不是直接给结论？
2. 原则提炼：回答中是否明确提炼了一条可复用的底层规律或框架？
3. 金句收尾：回答结尾是否有一句简洁有力的总结句，可以单独传播？
4. 无AI味：全文是否没有出现以下词汇：显而易见、值得注意、毋庸置疑、首先其次最后、综上所述、不言而喻？
5. 字数合理：回答是否在600-1800字之间？

待评估回答：
'

RESULTS='{"version":'$VERSION',"questions":[],"total_score":0}'
TOTAL=0

echo "Running eval for v${VERSION}..."

ALL_RESULTS="[]"
TOTAL_SCORE=0

for i in "${!QUESTIONS[@]}"; do
  Q="${QUESTIONS[$i]}"
  IDX=$((i+1))
  echo "  Q${IDX}: ${Q:0:30}..."
  
  # Generate answer
  ANSWER=$(claude -p "$SYSTEM_PROMPT" "$Q" --model claude-sonnet-4-5 2>/dev/null)
  
  # Score the answer
  EVAL_PROMPT="${EVAL_RULES}${ANSWER}"
  SCORE_JSON=$(claude -p "$EVAL_SYSTEM" "$EVAL_PROMPT" --model claude-sonnet-4-5 2>/dev/null)
  
  # Extract total from JSON
  SCORE_TOTAL=$(echo "$SCORE_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null || echo "0")
  TOTAL_SCORE=$((TOTAL_SCORE + SCORE_TOTAL))
  
  echo "    Score: ${SCORE_TOTAL}/5 | JSON: ${SCORE_JSON}"
  
  # Accumulate results
  Q_ESCAPED=$(echo "$Q" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))")
  A_ESCAPED=$(echo "$ANSWER" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))")
  
  ENTRY='{"question":'$Q_ESCAPED',"answer":'$A_ESCAPED',"eval":'$SCORE_JSON'}'
  
  if [ "$i" -eq 0 ]; then
    ALL_RESULTS="[$ENTRY"
  else
    ALL_RESULTS="$ALL_RESULTS,$ENTRY"
  fi
done

ALL_RESULTS="$ALL_RESULTS]"

# Write final JSON
python3 -c "
import json, sys
results = json.loads(sys.argv[1])
total = int(sys.argv[2])
output = {'version': int(sys.argv[3]), 'total_score': total, 'max_score': 50, 'questions': results}
print(json.dumps(output, ensure_ascii=False, indent=2))
" "$ALL_RESULTS" "$TOTAL_SCORE" "$VERSION" > "$OUTPUT_FILE"

echo "v${VERSION} total score: ${TOTAL_SCORE}/50"
echo "$TOTAL_SCORE"
