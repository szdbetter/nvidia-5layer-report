# 电商视频生成 — 复盘与SOP

**日期：** 2026-03-17  
**项目：** #电商频道 AI穿搭Vlog视频自动化生成  
**执行人：** Reese（AI）+ dbetter（老板）

---

## 一、背景与目标

老板需要用AI批量生成电商穿搭类Vlog视频素材，输入产品图，输出竖屏9:16的真实感穿搭展示视频，用于电商运营。工具选型：可灵AI（KlingAI）图生视频API。

---

## 二、踩坑记录与解决方案

### 坑1：API端点选错
- **错误：** 使用 `api.klingai.com`（全球端点）→ CN区Key认证失败（code 1002）
- **错误：** 使用 `api-cn.klingai.com`（CN端点）→ 后端502宕机
- **正确：** `https://api-beijing.klingai.com` ✅

### 坑2：认证方式理解错误
- **错误：** 把Secret Key直接当Bearer Token用 → `The token was expected to have 3 parts`
- **正确：** 必须生成JWT，payload含 `iss=API_KEY, exp=now+1800, nbf=now-5`，algorithm=HS256

### 坑3：图片太大导致上传超时
- **问题：** 模特图8.8MB → base64后~12MB → TCP write timeout
- **解决：** 用PIL压缩到100KB以下再上传（thumbnail(1200,2000) + quality=85）

### 坑4：虚拟试衣额度与视频额度不通
- **问题：** 调用 `/v1/images/kolors-virtual-try-on` → code 1102 余额不足
- **原因：** 视频额度（资源包）与虚拟试衣是独立计费，不互通
- **解决：** 跳过虚拟试衣，直接用产品图 + 文字描述服装做图生视频

### 坑5：新Key被禁用
- **现象：** 用户新建的Key `Aye38TkeAphC4AkLdH9dPry9H4TDg4yd` → `access key is disabled`
- **原因：** 新Key需要时间激活，或账号状态问题
- **解决：** 使用原有旧Key `AeR8a9nrbaDNhCRCbC44ETQFPpAhtkyP`

### 坑6：视频文件超Discord 8MB上传限制
- **解决：** ffmpeg用VP9压缩为.webm格式，`libvpx-vp9 -b:v 700-800k`（注：libx264在本服务器不可用）

### 坑7：Beijing端点网络抖动
- **现象：** Connection reset by peer，间歇性发生
- **解决：** 所有POST加重试逻辑（5次，指数退避）

---

## 三、最终可用的技术参数

| 参数 | 值 |
|------|-----|
| API端点 | `https://api-beijing.klingai.com` |
| 认证 | JWT（HS256），Bearer Token |
| API Key | `AeR8a9nrbaDNhCRCbC44ETQFPpAhtkyP` |
| API Secret | `CLhBpf4YN3dDg4hJB44RDGP3anfGhhyg` |
| 图片要求 | 压缩至100KB以下，base64传输 |
| 推荐模型 | `kling-v1-6` |
| 时长 | 5秒（标准）/ 10秒（详细展示） |
| 比例 | `9:16`（竖屏） |
| 模式 | `std`（标准） |
| cfg_scale | 0.5 |

---

## 四、有效提示词模板

```
这是一段手机实拍的竖屏（9:16）Vlog视频素材，画质保留轻微的手机传感器噪点与网络压缩痕迹，无美颜修饰、无滤镜，手持拍摄，带有自然的呼吸式微抖动。场景设定在略显杂乱的办公室门框处，背景包含真实的日常使用细节，光照来源于普通室内顶灯，光线均匀但不过度理想化，人物面部有自然的环境阴影。画面主体为一位年轻的亚洲女性，皮肤呈现真实纹理，面部肌肉放松，发丝边缘有生活化碎发。她身穿{outfit}，单肩挎着白色字母帆布包。她从画面远处自然走向镜头，步伐节奏有真实的人体运动变化，包含起步加速与停止时的身体重心起伏，拒绝匀速滑行。动作结束后短暂停留，面向镜头展示整体穿搭，表情为随意的微笑伴随自然眨眼，视线偶尔移向镜头外。视频以正常播放速度呈现，动作流畅连贯，拒绝慢动作。
```

**负面提示词：** `slow motion, beauty filter, studio lighting, CGI, cartoon, HDR, green screen, perfect skin, blur`

---

## 五、多款服装合并一个视频的方案

可灵不支持原生多场景，解决方案：
1. 每款服装单独生成一段视频（5秒/段）
2. ffmpeg concat拼接：`ffmpeg -f concat -safe 0 -i concat.txt -c copy output.mp4`
3. 若超8MB，用VP9压缩：`ffmpeg -c:v libvpx-vp9 -b:v 800k output.webm`

---

## 六、项目目录规范

- **项目根目录：** `/root/.openclaw/workspace/projects/e-commerce/`
- 所有产品图、视频、文档统一存放此处

---

## 七、标准化SOP（下次执行流程）

1. 收到产品图 → 下载并用PIL压缩到100KB以下，存入e-commerce目录
2. 确认服装描述 → 填入提示词模板
3. 调用KlingAI Beijing API，提交图生视频任务（加重试逻辑）
4. 轮询任务状态（15秒间隔，最大10分钟）
5. 下载视频到e-commerce目录
6. 如需合并：ffmpeg concat → vp9压缩
7. 通过message工具发送到Discord频道
