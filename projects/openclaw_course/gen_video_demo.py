#!/usr/bin/env python3
"""Generate PPT video demo: oatmeal slides + TTS narration → MP4"""
import asyncio, subprocess, os

PROJECT = "/root/.openclaw/workspace/projects/openclaw_course"
OUT_DIR = "/root/.openclaw/workspace/projects/openclaw_course/video_output"
os.makedirs(OUT_DIR, exist_ok=True)

NARRATIONS = [
    "各位老板，我先问一个问题：你现在的竞争对手是谁？是隔壁公司？是跨界的新玩家？我说，都不是。2026年，你最大的竞争对手，是那些已经把AI变成员工的人。他们一天干完你一周的活，一人顶十人的产出。这不是未来，这是正在发生的现实。今天不讲技术，讲一件事：你如何从用AI的人变成AI的老板。",
    "我们来做个算术题。你用ChatGPT、豆包、文心一言，帮你写方案、做分析、出主意。这些AI值多少钱？如果按年薪算，它们相当于一个年薪百万的顶级参谋。但问题来了——参谋出主意，谁来执行？还是你。你问它怎么做，它告诉你答案，然后你打字、做表、发邮件、跟进。你雇了一个百万年薪的军师，却天天自己跑腿。这不是用AI，这是给AI打工。",
    "让我用一句话说清楚这个变革。过去两年的AI，本质上只有大脑——它能思考、推理、生成内容，但它不能自己执行。你想让它帮你订票？它告诉你方法，然后你自己打开App去订。Agent的出现，让AI长出了手脚。它能自己拆解任务、调用工具、执行操作、遇到问题自己修正。AI终于从大脑进化成完整的人——会想，也会干。",
    "2026年，所有人都会用AI，但只有少数人能驾驭AI。什么叫驾驭？就是你只需要说一句话，它自己把活干完。什么叫会用？就是你问它问题，它给你答案，然后你自己去执行。这两者的差距，不是技术，是认知。一年后，两类人的差距会拉大到什么程度？一类人已经拥有了自己的数字团队，另一类人还在每天和AI聊天。认知差，就是财富差。",
    "来看一个真实案例。Arcads AI，一家做广告营销的公司，团队只有6个人。他们的年营收是多少？人均279万美元。怎么做到的？他们的广告投放、竞价优化、客户跟进、数据分析，全部交给AI Agent执行。6个人，干出了传统30人团队的业绩。他们的CEO说：我最重要的工作，不是管人，而是管Agent。这就是数字员工的力量——不是替代你，而是放大你。",
    "再来看另一个案例。Maor Shlomo，Base44的创始人，一个人开发了一款产品，成立6个月就被Wix以8000万美元收购。他怎么做到的？他几乎不写代码——所有代码由AI Agent生成。他的核心竞争力是什么？不是技术能力，而是让AI干活的能力。他像一个指挥官，Agent是他的执行团队。这是超级个体的时代——一个人，加上AI，可以对抗一个公司。",
    "这不是一个技术趋势，这是一个国家战略。2026年政府工作报告，首次把智能体写进去。国务院明确目标：到2027年，智能体应用普及率超过70%。什么意思？国家已经帮你把方向定好了。六大巨头——腾讯、阿里、字节、百度、华为、火山引擎，全部下场。周鸿祎说：未来的核心竞争，聚焦于智能体生态。你不需要猜方向，方向已经确定，现在的问题是：你跟不跟？",
    "看看现在的市场格局。字节跳动有豆包和扣子平台，适合做营销获客；腾讯有元宝和元器，微信生态天然优势；阿里有夸克和通义，电商和企业服务是强项；百度有文心，搜索入口加上多智能体群聊；华为有盘古，政企和工业场景安全合规。六大巨头已经入场，平台生态已经成型。对企业老板来说，选对平台，比自建更重要。不用从头造轮子，搭上巨头的便车，才是最快的路径。",
    "数字员工到底能干什么？我举几个已经落地的场景。信息收割——有个投资人，每天早上醒来，微信里已经躺着一份行业简报，昨晚全球AI赛道的融资动态、竞品动作、政策变化，全部自动整理。内容生产——一个自媒体人，用Agent搭建内容流水线，一个人同时运营五个平台，产量翻五倍，投入时间反而减少。流程自动化——客服、销售跟进、数据分析，这些重复性工作，Agent都能接管。你说，你的团队有多少时间耗在这些事上？",
    "数字员工不是万能的。它没有价值观——你让它干什么，它就干什么，但它不会告诉你这事该不该干。它没有审美——它能生成内容，但不能判断内容好不好。它没有战略判断——它能执行计划，但不能制定方向。所以，你的核心竞争力是什么？是战略眼光、审美判断、人情洞察。AI是工具，你是指挥官。用好工具的前提，是你先想清楚方向。",
    "听完今天的内容，你该做什么？三件事。第一步，盘点——找出你工作流中最重复、最耗时的部分，那些让你觉得这事不该我干的事。第二步，选择——根据你的场景选择平台。营销获客，看字节和腾讯；企业服务，看阿里和华为；搜索和多智能体，看百度。第三步，行动——用Agent替代这些工作，把你的时间释放出来。不要等，今年布局，明年就领先。明年再动，就晚了。",
    "最后，我想送给大家一句话。下一个时代，你要么拥有自己的数字员工，要么成为别人数字员工的工具。这不是危言耸听，而是正在发生的现实。AI不会取代人，但会用AI的人，一定会取代不会用的人。2026年是窗口期，天时地利人和——政策支持、技术成熟、巨头入场。错过这一年，就是十年的差距。如果你准备好了，欢迎来到数字员工元年。谢谢大家。",
]

VOICE = "zh-CN-YunxiNeural"

async def gen_tts(idx, text):
    out = f"{OUT_DIR}/slide_{idx+1:02d}.mp3"
    if os.path.exists(out):
        return out
    import edge_tts
    comm = edge_tts.Communicate(text, VOICE, rate="+5%")
    await comm.save(out)
    print(f"  ✅ TTS slide {idx+1}")
    return out

def get_duration(f):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", f],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

async def main():
    print("🎤 Generating TTS for 12 slides...")
    tasks = [gen_tts(i, t) for i, t in enumerate(NARRATIONS)]
    audio_files = await asyncio.gather(*tasks)

    print("\n🎬 Building video with ffmpeg...")
    inputs = []
    filter_parts = []
    concat_parts = []

    for i in range(12):
        img = f"{PROJECT}/oatmeal-preview-{i+1:02d}.png"
        dur = get_duration(audio_files[i])
        inputs.extend(["-loop", "1", "-t", str(dur), "-i", img])
        inputs.extend(["-i", audio_files[i]])
        vi = i * 2
        ai = i * 2 + 1
        filter_parts.append(f"[{vi}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1,fps=30[v{i}]")
        concat_parts.append(f"[v{i}][{ai}:a]")

    fc = ";".join(filter_parts)
    fc += f";{''.join(concat_parts)}concat=n=12:v=1:a=1[outv][outa]"

    out_file = f"{OUT_DIR}/demo_oatmeal.mp4"
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", fc,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "mpeg4", "-q:v", "5",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out_file
    ]

    print(f"  Running ffmpeg...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"❌ ffmpeg error:\n{r.stderr[-2000:]}")
        return

    size_mb = os.path.getsize(out_file) / 1024 / 1024
    total_dur = get_duration(out_file)
    print(f"\n✅ Done! Output: {out_file} ({size_mb:.1f} MB, {total_dur:.1f}s / {total_dur/60:.1f}min)")

if __name__ == "__main__":
    asyncio.run(main())
