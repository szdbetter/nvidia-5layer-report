#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub仓库文件处理脚本：适配Notebook LLM
核心功能：自动下载仓库 + 筛选核心文件 + 保留原始结构 + 合并为MD文件（带进度提示）
运行环境：Python 3.11+
依赖说明：
1. 基础依赖：pip install requests nbformat
2. 可选系统依赖（处理.rst）：pandoc → https://pandoc.org/installing.html
"""

import os
import sys
import shutil
import logging
import subprocess
import datetime  # 新增：用于生成日期后缀
import hashlib
import importlib
import importlib.util
import configparser
from collections import deque
from pathlib import Path
from typing import List, Dict, Tuple, Set, Deque
import json
import zipfile  # 新增：用于解压GitHub ZIP包

requests = None
Progress = None
SpinnerColumn = None
BarColumn = None
TextColumn = None
TimeElapsedColumn = None
TimeRemainingColumn = None
DownloadColumn = None
TransferSpeedColumn = None
Console = None
Panel = None
Table = None
Layout = None
Live = None
RICH_AVAILABLE = False

# ======================== 【核心修复】全局变量提前声明 + 日志初始化 ========================
# 提前声明全局变量，避免后续函数引用时报错
logger = None
SOURCE_DIR = None
OUTPUT_ROOT = None  # 修改：从固定值改为动态赋值
PROJECT_NAME = None  # 新增：存储仓库项目名（剔除用户名）

# 忽略的目录/文件（支持通配符和精确匹配）
IGNORE_PATTERNS = [
    ".git", "__pycache__", "venv", ".github",
    ".gitignore", "requirements.txt", "*.png", "*.jpg", "*.zip", "*.tar.gz"
]
# 核心处理的文件类型（key=类型分组，value=后缀列表）
CORE_FILE_TYPES = {
    "docs": [".md", ".rst", ".txt", ".adoc"],  # 文档类
    "code": [
        ".py", ".ipynb", ".js", ".jsx", ".mjs", ".cjs",
        ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".swift",
        ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb",
        ".sh", ".bash", ".zsh", ".ps1",
        ".yaml", ".yml", ".toml", ".json", ".ini", ".cfg", ".conf",
        ".xml", ".html", ".css", ".scss", ".vue", ".svelte", ".dart", ".lua", ".sql"
    ],  # 代码类
}
# 合并文件大小阈值（MB）：单文件超过该值则拆分成分卷
MERGE_SIZE_THRESHOLD_MB = 5
# 编码格式（固定utf-8）
ENCODING = "utf-8"
# GitHub默认分支（可根据需求修改）
GITHUB_DEFAULT_BRANCH = "main"
# 默认仓库（用户直接回车时使用）
DEFAULT_GITHUB_REPO = "openclaw/openclaw"
# 合并输出是否按大小拆分（False = docs一个文件 + code一个文件）
SPLIT_MERGED_FILES = False
OUTPUT_BASE_DIR = "."
OUTPUT_NAME_TEMPLATE = "{project}"
# 最低Python版本要求
MIN_PYTHON_VERSION = (3, 11)
# 运行所需依赖（模块名: pip包名）
REQUIRED_PACKAGES = {
    "requests": "requests",
    "nbformat": "nbformat",
    "rich": "rich",
}
TUI_ENABLED = True
TUI_MAX_EVENTS = 12

SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = SCRIPT_DIR / "get_github_files.ini"
DASHBOARD = None


def setup_global_logger():
    """初始化全局日志（脚本启动就加载，确保全程可用）"""
    global logger
    # 先创建临时日志目录（避免日志文件写入失败）
    temp_log_dir = SCRIPT_DIR / "temp_log"
    temp_log_dir.mkdir(parents=True, exist_ok=True)

    # 重置已有logger（避免重复配置）
    if logger is not None:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # 控制台输出
            logging.FileHandler(temp_log_dir / "temp_process.log", encoding="utf-8")  # 临时日志文件
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("全局日志初始化完成")


# 立即执行日志初始化（脚本启动就加载，优先级最高）
setup_global_logger()


def write_default_config(config_path: Path) -> None:
    """写入默认配置文件（首次运行自动生成）"""
    default_text = """[github]
default_repo = openclaw/openclaw
default_branch = main

[output]
encoding = utf-8
merge_size_threshold_mb = 5
split_merged_files = false
output_base_dir = .
output_name_template = {project}

[filter]
ignore_patterns = .git,__pycache__,venv,.github,.gitignore,requirements.txt,*.png,*.jpg,*.zip,*.tar.gz
docs_ext = .md,.rst,.txt,.adoc
code_ext = .py,.ipynb,.js,.jsx,.mjs,.cjs,.ts,.tsx,.go,.rs,.java,.kt,.swift,.c,.cc,.cpp,.h,.hpp,.cs,.php,.rb,.sh,.bash,.zsh,.ps1,.yaml,.yml,.toml,.json,.ini,.cfg,.conf,.xml,.html,.css,.scss,.vue,.svelte,.dart,.lua,.sql

[runtime]
min_python_version = 3.11
required_packages = requests,nbformat,rich

[tui]
enabled = true
max_events = 12
"""
    config_path.write_text(default_text, encoding="utf-8")


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config(config_path: Path = CONFIG_FILE) -> None:
    """从INI加载配置，缺省时生成默认配置"""
    global DEFAULT_GITHUB_REPO, GITHUB_DEFAULT_BRANCH, ENCODING
    global MERGE_SIZE_THRESHOLD_MB, SPLIT_MERGED_FILES, OUTPUT_BASE_DIR, OUTPUT_NAME_TEMPLATE
    global IGNORE_PATTERNS, CORE_FILE_TYPES
    global MIN_PYTHON_VERSION, REQUIRED_PACKAGES
    global TUI_ENABLED, TUI_MAX_EVENTS

    if not config_path.exists():
        write_default_config(config_path)
        logger.info(f"未找到配置文件，已自动创建默认配置：{config_path}")

    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")

    DEFAULT_GITHUB_REPO = parser.get("github", "default_repo", fallback=DEFAULT_GITHUB_REPO)
    GITHUB_DEFAULT_BRANCH = parser.get("github", "default_branch", fallback=GITHUB_DEFAULT_BRANCH)

    ENCODING = parser.get("output", "encoding", fallback=ENCODING)
    MERGE_SIZE_THRESHOLD_MB = parser.getint("output", "merge_size_threshold_mb", fallback=MERGE_SIZE_THRESHOLD_MB)
    SPLIT_MERGED_FILES = parser.getboolean("output", "split_merged_files", fallback=SPLIT_MERGED_FILES)
    OUTPUT_BASE_DIR = parser.get("output", "output_base_dir", fallback=OUTPUT_BASE_DIR)
    OUTPUT_NAME_TEMPLATE = parser.get("output", "output_name_template", fallback=OUTPUT_NAME_TEMPLATE)

    IGNORE_PATTERNS = _split_csv(parser.get("filter", "ignore_patterns", fallback=",".join(IGNORE_PATTERNS)))
    docs_ext = _split_csv(parser.get("filter", "docs_ext", fallback=",".join(CORE_FILE_TYPES["docs"])))
    code_ext = _split_csv(parser.get("filter", "code_ext", fallback=",".join(CORE_FILE_TYPES["code"])))
    CORE_FILE_TYPES = {"docs": docs_ext, "code": code_ext}

    min_ver = parser.get("runtime", "min_python_version", fallback=f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
    try:
        major, minor = min_ver.strip().split(".", 1)
        MIN_PYTHON_VERSION = (int(major), int(minor))
    except Exception:
        logger.warning(f"配置项 min_python_version 无效：{min_ver}，已回退默认值")

    required = _split_csv(parser.get("runtime", "required_packages", fallback="requests,nbformat,rich"))
    REQUIRED_PACKAGES = {pkg: pkg for pkg in required}

    TUI_ENABLED = parser.getboolean("tui", "enabled", fallback=TUI_ENABLED)
    TUI_MAX_EVENTS = parser.getint("tui", "max_events", fallback=TUI_MAX_EVENTS)


def init_rich_support() -> None:
    """初始化rich进度条支持（可在安装依赖后重复调用）"""
    global RICH_AVAILABLE, Progress, SpinnerColumn, BarColumn, TextColumn
    global TimeElapsedColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
    global Console, Panel, Table, Layout, Live
    try:
        from rich.progress import (
            Progress as _Progress,
            SpinnerColumn as _SpinnerColumn,
            BarColumn as _BarColumn,
            TextColumn as _TextColumn,
            TimeElapsedColumn as _TimeElapsedColumn,
            TimeRemainingColumn as _TimeRemainingColumn,
            DownloadColumn as _DownloadColumn,
            TransferSpeedColumn as _TransferSpeedColumn,
        )
        from rich.console import Console as _Console
        from rich.panel import Panel as _Panel
        from rich.table import Table as _Table
        from rich.layout import Layout as _Layout
        from rich.live import Live as _Live
        Progress = _Progress
        SpinnerColumn = _SpinnerColumn
        BarColumn = _BarColumn
        TextColumn = _TextColumn
        TimeElapsedColumn = _TimeElapsedColumn
        TimeRemainingColumn = _TimeRemainingColumn
        DownloadColumn = _DownloadColumn
        TransferSpeedColumn = _TransferSpeedColumn
        Console = _Console
        Panel = _Panel
        Table = _Table
        Layout = _Layout
        Live = _Live
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False


class TerminalDashboard:
    """基于rich.Live的单屏Dashboard"""

    def __init__(self, max_events: int = 12):
        self.console = Console()
        self.live = None
        self.max_events = max_events
        self.events: Deque[str] = deque(maxlen=max_events)
        self.repo_name = "-"
        self.output_dir = "-"
        self.current_stage = "初始化"
        self.stages: Dict[str, Dict[str, str]] = {
            "env": {"name": "环境检查", "status": "等待", "progress": "-", "detail": "-"},
            "download": {"name": "下载仓库", "status": "等待", "progress": "-", "detail": "-"},
            "scan": {"name": "扫描筛选", "status": "等待", "progress": "-", "detail": "-"},
            "sync": {"name": "增量同步", "status": "等待", "progress": "-", "detail": "-"},
            "merge": {"name": "合并输出", "status": "等待", "progress": "-", "detail": "-"},
        }

    def start(self) -> None:
        self.live = Live(self.render(), refresh_per_second=8, console=self.console)
        self.live.start()

    def stop(self) -> None:
        if self.live is not None:
            self.live.stop()
            self.live = None

    def set_context(self, repo_name: str = None, output_dir: str = None, current_stage: str = None) -> None:
        if repo_name is not None:
            self.repo_name = repo_name
        if output_dir is not None:
            self.output_dir = output_dir
        if current_stage is not None:
            self.current_stage = current_stage
        self.refresh()

    def update_stage(
        self, key: str, status: str = None, completed: int = None, total: int = None, detail: str = None
    ) -> None:
        if key not in self.stages:
            return
        if status is not None:
            self.stages[key]["status"] = status
        if completed is not None and total is not None and total > 0:
            pct = int((completed / total) * 100)
            self.stages[key]["progress"] = f"{completed}/{total} ({pct}%)"
        elif completed == 0 and total == 0:
            self.stages[key]["progress"] = "0/0"
        if detail is not None:
            self.stages[key]["detail"] = detail
        self.refresh()

    def log_event(self, message: str) -> None:
        self.events.appendleft(message)
        self.refresh()

    def render(self):
        header = Table.grid(expand=True)
        header.add_column(justify="left")
        header.add_column(justify="right")
        header.add_row("[bold cyan]GitHub 文档抓取 Dashboard[/bold cyan]", f"[bold]阶段:[/bold] {self.current_stage}")
        header.add_row(f"[bold]仓库:[/bold] {self.repo_name}", f"[bold]输出:[/bold] {self.output_dir}")

        stage_table = Table(expand=True)
        stage_table.add_column("模块", style="cyan", no_wrap=True)
        stage_table.add_column("状态", style="green")
        stage_table.add_column("进度", style="magenta")
        stage_table.add_column("详情", style="white")
        for stage in self.stages.values():
            stage_table.add_row(stage["name"], stage["status"], stage["progress"], stage["detail"])

        events_table = Table(expand=True)
        events_table.add_column("最近事件", style="yellow")
        if self.events:
            for event in self.events:
                events_table.add_row(event)
        else:
            events_table.add_row("-")

        layout = Layout()
        layout.split_column(
            Layout(Panel(header, border_style="cyan"), size=5),
            Layout(Panel(stage_table, title="执行状态", border_style="green"), ratio=3),
            Layout(Panel(events_table, title="事件日志", border_style="yellow"), ratio=2),
        )
        return layout

    def refresh(self) -> None:
        if self.live is not None:
            self.live.update(self.render())


def ui_update_stage(
    key: str, status: str = None, completed: int = None, total: int = None, detail: str = None
) -> None:
    if DASHBOARD is not None:
        DASHBOARD.update_stage(key, status=status, completed=completed, total=total, detail=detail)


def ui_set_context(repo_name: str = None, output_dir: str = None, current_stage: str = None) -> None:
    if DASHBOARD is not None:
        DASHBOARD.set_context(repo_name=repo_name, output_dir=output_dir, current_stage=current_stage)


def ui_log(message: str) -> None:
    if DASHBOARD is not None:
        DASHBOARD.log_event(message)


def build_output_root(repo_name: str) -> str:
    """根据配置生成输出目录，支持相对/绝对路径"""
    repo_slug = repo_name.replace("/", "_")
    try:
        folder_name = OUTPUT_NAME_TEMPLATE.format(
            repo=repo_name,
            repo_slug=repo_slug,
            owner=repo_name.split("/")[0],
            project=repo_name.split("/")[1] if "/" in repo_name else repo_slug,
        )
    except Exception:
        folder_name = f"{repo_slug}_LLM_Processed"

    base_dir = Path(OUTPUT_BASE_DIR).expanduser()
    if not base_dir.is_absolute():
        base_dir = (SCRIPT_DIR / base_dir).resolve()
    return str(base_dir / folder_name)


def calculate_dir_metrics(dir_path: Path) -> Dict[str, int]:
    """统计目录文件数和总大小（字节）"""
    if not dir_path.exists():
        return {"files": 0, "bytes": 0}
    file_count = 0
    total_bytes = 0
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            file_count += 1
            total_bytes += file_path.stat().st_size
    return {"files": file_count, "bytes": total_bytes}


def format_bytes(size_in_bytes: int) -> str:
    """把字节数格式化为可读大小"""
    sign = "-" if size_in_bytes < 0 else ""
    size_in_bytes = abs(size_in_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_in_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{sign}{size:.2f}{unit}"
        size /= 1024
    return f"{sign}{size_in_bytes}B"


def ensure_runtime_environment() -> None:
    """启动时检查Python3与依赖，缺失依赖自动安装"""
    global requests

    logger.info("开始环境检查：Python3 与依赖包")
    ui_set_context(current_stage="环境检查")
    ui_update_stage("env", status="进行中", detail="检查 Python3 / pip / 依赖")

    if shutil.which("python3") is None:
        ui_update_stage("env", status="失败", detail="未检测到 python3")
        logger.error("未检测到 python3，请先安装 Python 3.11+ 后再运行脚本。")
        logger.error("macOS 可执行：brew install python@3.11")
        sys.exit(1)

    if sys.version_info < MIN_PYTHON_VERSION:
        version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ui_update_stage("env", status="失败", detail=f"Python版本过低：{version_str}")
        logger.error(f"当前Python版本过低：{version_str}，需要 >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
        logger.error("请先安装 Python 3.11+ 后再运行脚本。")
        sys.exit(1)

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        ui_update_stage("env", status="失败", detail="pip 不可用")
        logger.error("检测到当前Python环境缺少 pip。请先重新安装 Python3（自带pip）后再运行。")
        sys.exit(1)

    missing_packages: List[str] = []
    for module_name, package_name in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)

    if missing_packages:
        ui_log(f"自动安装依赖：{', '.join(missing_packages)}")
        logger.warning(f"检测到缺失依赖，开始自动安装：{', '.join(missing_packages)}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", *missing_packages],
                check=True,
            )
        except subprocess.CalledProcessError:
            ui_update_stage("env", status="失败", detail="依赖自动安装失败")
            logger.error("自动安装依赖失败。请手动执行：")
            logger.error(f"{sys.executable} -m pip install {' '.join(missing_packages)}")
            sys.exit(1)

    try:
        requests = importlib.import_module("requests")
    except Exception:
        ui_update_stage("env", status="失败", detail="requests 加载失败")
        logger.error("无法加载 requests 模块，请检查Python环境后重试。")
        sys.exit(1)

    init_rich_support()
    logger.info("环境检查通过")
    ui_update_stage("env", status="完成", detail="环境检查通过")


# ======================== 新增：自动下载GitHub仓库函数 ========================
def download_github_repo(repo_name: str) -> Path:
    """
    自动下载GitHub仓库ZIP包并解压
    :param repo_name: GitHub仓库名（格式：用户名/仓库名）
    :return: 解压后的仓库根目录路径
    """
    global PROJECT_NAME
    # 解析仓库用户名和仓库名
    try:
        owner, PROJECT_NAME = repo_name.strip().split("/")  # 提取项目名到全局变量
    except ValueError:
        logger.error("仓库名格式错误！请输入：用户名/仓库名（例如：octocat/hello-world）")
        sys.exit(1)

    # 构建下载链接和临时文件路径
    zip_url = f"https://github.com/{owner}/{PROJECT_NAME}/archive/refs/heads/{GITHUB_DEFAULT_BRANCH}.zip"
    script_dir = Path(__file__).parent.absolute()
    temp_zip = script_dir / f"{PROJECT_NAME}_{GITHUB_DEFAULT_BRANCH}.zip"
    extract_root = script_dir / "temp_github_repo"  # 临时解压目录

    # 下载ZIP包
    logger.info(f"开始下载GitHub仓库：{repo_name}（分支：{GITHUB_DEFAULT_BRANCH}）")
    ui_set_context(current_stage="下载仓库")
    ui_update_stage("download", status="进行中", detail=f"{repo_name}@{GITHUB_DEFAULT_BRANCH}")
    ui_log(f"开始下载仓库：{repo_name}")
    try:
        response = requests.get(
            zip_url,
            stream=True,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0
        last_update_bytes = 0

        # 流式写入ZIP文件（显示整体下载进度）
        with open(temp_zip, "wb") as f:
            if DASHBOARD is not None and total_size > 0:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if downloaded_size - last_update_bytes >= 256 * 1024 or downloaded_size == total_size:
                        ui_update_stage(
                            "download",
                            completed=downloaded_size,
                            total=total_size,
                            detail=f"{downloaded_size / 1024 / 1024:.2f}MB / {total_size / 1024 / 1024:.2f}MB",
                        )
                        last_update_bytes = downloaded_size
            elif RICH_AVAILABLE and total_size > 0:
                with Progress(
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task_id = progress.add_task("下载仓库ZIP", total=total_size)
                    for chunk in response.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress.update(task_id, advance=len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded_size += len(chunk)
        logger.info(f"ZIP包下载完成：{temp_zip}")
        if total_size > 0:
            ui_update_stage("download", status="完成", completed=total_size, total=total_size, detail="下载完成")
        else:
            ui_update_stage("download", status="完成", detail="下载完成")
        ui_log("仓库压缩包下载完成")

        # 解压ZIP包
        extract_root.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(temp_zip, "r") as zf:
            zf.extractall(extract_root)
        logger.info(f"ZIP包解压完成：{extract_root}")
        ui_log("ZIP 解压完成")

        # 删除临时ZIP文件
        os.remove(temp_zip)
        logger.info(f"临时ZIP文件已清理：{temp_zip}")

        # 找到解压后的仓库根目录（GitHub ZIP解压后会带「仓库名-分支名」后缀）
        repo_root_list = list(extract_root.glob(f"{PROJECT_NAME}-{GITHUB_DEFAULT_BRANCH}"))
        if not repo_root_list:
            raise FileNotFoundError(f"解压后未找到仓库目录：{PROJECT_NAME}-{GITHUB_DEFAULT_BRANCH}")
        repo_root = repo_root_list[0]
        return repo_root

    except requests.exceptions.RequestException as e:
        ui_update_stage("download", status="失败", detail=str(e))
        logger.error(f"仓库下载失败：{str(e)}")
        sys.exit(1)
    except zipfile.BadZipFile as e:
        ui_update_stage("download", status="失败", detail=f"ZIP损坏: {str(e)}")
        logger.error(f"ZIP包损坏：{str(e)}")
        sys.exit(1)
    except Exception as e:
        ui_update_stage("download", status="失败", detail=str(e))
        logger.error(f"解压/清理失败：{str(e)}", exc_info=True)
        sys.exit(1)


# ======================== 原有工具函数（修复全局变量引用）========================
def is_binary_file(file_path: Path) -> bool:
    """判断文件是否为二进制文件"""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk  # 二进制文件通常包含空字节
    except Exception:
        return True


def is_empty_file(file_path: Path) -> bool:
    """判断文件是否为空"""
    return file_path.stat().st_size == 0


def calculate_file_sha256(file_path: Path) -> str:
    """计算文件SHA256，用于内容级别增量判断"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def is_same_file_content(src_path: Path, dst_path: Path) -> bool:
    """判断两个文件内容是否一致（先比大小，再比哈希）"""
    if not dst_path.exists() or not dst_path.is_file():
        return False
    if src_path.stat().st_size != dst_path.stat().st_size:
        return False
    return calculate_file_sha256(src_path) == calculate_file_sha256(dst_path)


def match_ignore_pattern(file_path: Path, ignore_patterns: List[str]) -> bool:
    """判断文件/目录是否匹配忽略规则"""
    global SOURCE_DIR  # 显式引用全局变量
    if SOURCE_DIR is None or not SOURCE_DIR.exists():
        return True
    rel_path = file_path.relative_to(SOURCE_DIR) if SOURCE_DIR in file_path.parents else file_path
    rel_path_str = str(rel_path).replace("\\", "/")  # 统一路径分隔符

    for pattern in ignore_patterns:
        # 精确匹配文件/目录名
        if pattern == file_path.name or pattern == str(rel_path):
            return True
        # 通配符匹配（简单实现*后缀）
        if pattern.startswith("*.") and rel_path_str.endswith(pattern[1:]):
            return True
        # 目录包含匹配
        if Path(pattern) in file_path.parents:
            return True
    return False


def filter_core_files(source_dir: str) -> Dict[str, List[Path]]:
    """
    筛选核心文件，按类型分组
    返回：{"docs": [文件路径列表], "code": [文件路径列表]}
    """
    source_path = Path(source_dir)
    if not source_path.exists():
        logger.error(f"源目录不存在：{source_dir}")
        sys.exit(1)

    filtered_files: Dict[str, List[Path]] = {"docs": [], "code": []}
    total_scanned = 0
    valid_files = 0

    logger.info("开始筛选核心文件...")
    ui_set_context(current_stage="扫描筛选")
    ui_update_stage("scan", status="进行中", detail="遍历仓库文件")
    all_file_paths: List[Path] = []
    for root, _, files in os.walk(source_dir):
        root_path = Path(root)
        for file in files:
            all_file_paths.append(root_path / file)

    total_scanned = len(all_file_paths)

    def process_one_file(file_path: Path) -> None:
        nonlocal valid_files
        # 跳过忽略的文件/二进制文件/空文件
        if match_ignore_pattern(file_path, IGNORE_PATTERNS):
            return
        if is_binary_file(file_path):
            return
        if is_empty_file(file_path):
            return

        # 按类型分组
        file_suffix = file_path.suffix.lower()
        if file_suffix in CORE_FILE_TYPES["docs"]:
            filtered_files["docs"].append(file_path)
            valid_files += 1
        elif file_suffix in CORE_FILE_TYPES["code"]:
            filtered_files["code"].append(file_path)
            valid_files += 1

    if DASHBOARD is not None and total_scanned > 0:
        for idx, file_path in enumerate(all_file_paths, 1):
            process_one_file(file_path)
            if idx % 10 == 0 or idx == total_scanned:
                ui_update_stage("scan", completed=idx, total=total_scanned, detail=f"有效文件: {valid_files}")
    elif RICH_AVAILABLE and total_scanned > 0:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold magenta]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task("扫描并筛选核心文件", total=total_scanned)
            for file_path in all_file_paths:
                process_one_file(file_path)
                progress.update(task_id, advance=1)
    else:
        for file_path in all_file_paths:
            process_one_file(file_path)

    logger.info(f"文件筛选完成：共扫描{total_scanned}个文件，筛选出{valid_files}个核心文件")
    logger.info(f"文档类文件数：{len(filtered_files['docs'])} | 代码类文件数：{len(filtered_files['code'])}")
    ui_update_stage("scan", status="完成", completed=total_scanned, total=total_scanned, detail=f"有效: {valid_files}")
    ui_log(f"扫描完成：文档{len(filtered_files['docs'])}，代码{len(filtered_files['code'])}")
    return filtered_files


def copy_original_files(filtered_files: Dict[str, List[Path]]) -> None:
    """
    模式1：保留原始文件结构到original_files目录
    """
    global SOURCE_DIR, OUTPUT_ROOT
    original_dir = Path(OUTPUT_ROOT) / "original_files"
    original_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"\n开始复制原始文件到：{original_dir}")
    ui_set_context(current_stage="增量同步")
    ui_update_stage("sync", status="进行中", detail="对比并同步文件")

    # 合并所有筛选后的文件
    all_files = filtered_files["docs"] + filtered_files["code"]
    total_files = len(all_files)
    copied_count = 0
    unchanged_count = 0
    updated_count = 0
    new_count = 0
    kept_rel_paths: Set[Path] = set()

    def process_one_file(file_path: Path) -> None:
        nonlocal copied_count, unchanged_count, updated_count, new_count
        rel_path = file_path.relative_to(SOURCE_DIR)
        target_path = original_dir / rel_path
        kept_rel_paths.add(rel_path)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if is_same_file_content(file_path, target_path):
                unchanged_count += 1
                return
            target_existed = target_path.exists()
            shutil.copy2(file_path, target_path)
            copied_count += 1
            if target_existed:
                updated_count += 1
            else:
                new_count += 1
        except Exception as e:
            logger.error(f"复制失败：{file_path} | 错误：{str(e)}", exc_info=False)

    # 文件对比+同步整体进度（不刷屏逐文件日志）
    if DASHBOARD is not None and total_files > 0:
        for idx, file_path in enumerate(all_files, 1):
            process_one_file(file_path)
            if idx % 10 == 0 or idx == total_files:
                ui_update_stage(
                    "sync",
                    completed=idx,
                    total=total_files,
                    detail=f"新增{new_count} 更新{updated_count} 未变{unchanged_count}",
                )
    elif RICH_AVAILABLE and total_files > 0:
        with Progress(
            TextColumn("[bold green]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task("文件对比与增量同步", total=total_files)
            for file_path in all_files:
                process_one_file(file_path)
                progress.update(task_id, advance=1)
    else:
        for file_path in all_files:
            process_one_file(file_path)

    # 删除本地已不存在的旧文件，保证original_files只保留最新版本
    deleted_count = 0
    for existing_file in original_dir.rglob("*"):
        if existing_file.is_file():
            rel_path = existing_file.relative_to(original_dir)
            if rel_path not in kept_rel_paths:
                try:
                    existing_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"删除旧文件失败：{existing_file} | 错误：{str(e)}", exc_info=False)

    # 清理空目录（从深到浅）
    for dir_path in sorted(original_dir.rglob("*"), reverse=True):
        if dir_path.is_dir():
            try:
                dir_path.rmdir()
            except OSError:
                pass

    logger.info(
        "原始文件增量更新完成："
        f"总计{total_files}个 | 新增{new_count}个 | 更新{updated_count}个 | "
        f"未变化{unchanged_count}个 | 删除旧文件{deleted_count}个 | 目录：{original_dir}"
    )
    logger.info(f"本次实际更新文件数：{new_count + updated_count + deleted_count}个")
    ui_update_stage(
        "sync",
        status="完成",
        completed=total_files,
        total=total_files,
        detail=f"新增{new_count} 更新{updated_count} 删除{deleted_count}",
    )
    ui_log(f"增量同步完成：更新{new_count + updated_count + deleted_count}个文件")


def convert_to_md(file_path: Path) -> str:
    """
    转换各类文件为MD格式字符串
    返回：转换后的MD内容
    """
    global SOURCE_DIR
    suffix = file_path.suffix.lower()
    file_rel_path = file_path.relative_to(SOURCE_DIR)

    # 基础MD头部（标注文件信息）
    md_header = f"\n=== 文件名：{file_rel_path} | 类型：{suffix} ===\n"

    try:
        # 1. Markdown文件（直接读取）
        if suffix == ".md":
            with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                content = f.read()
            return md_header + content + "\n=== 该文件结束 ===\n"

        # 2. 纯文本文件（直接封装为MD）
        elif suffix == ".txt":
            with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                content = f.read()
            return md_header + f"\n{content}\n" + "=== 该文件结束 ===\n"

        # 3. Python文件（封装为代码块）
        elif suffix == ".py":
            with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                code = f.read()
            return md_header + f"\n```python\n{code}\n```\n" + "=== 该文件结束 ===\n"

        # 4. RST文件（用pandoc转换）
        elif suffix == ".rst":
            try:
                result = subprocess.run(
                    ["pandoc", "-s", str(file_path), "-t", "markdown"],
                    capture_output=True, encoding=ENCODING, errors="ignore"
                )
                if result.returncode == 0:
                    return md_header + result.stdout + "\n=== 该文件结束 ===\n"
                else:
                    logger.warning(f"RST转换失败：{file_path} | 降级为纯文本读取")
                    with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                        content = f.read()
                    return md_header + f"\n{content}\n" + "=== 该文件结束 ===\n"
            except FileNotFoundError:
                logger.warning(f"未找到pandoc，RST文件{file_path}降级为纯文本读取")
                with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                    content = f.read()
                return md_header + f"\n{content}\n" + "=== 该文件结束 ===\n"

        # 5. IPYNB文件（提取markdown+代码块）
        elif suffix == ".ipynb":
            try:
                import nbformat
                with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                    nb = nbformat.read(f, as_version=4)

                ipynb_content = []
                for cell in nb.cells:
                    if cell.cell_type == "markdown":
                        ipynb_content.append(cell.source)
                    elif cell.cell_type == "code":
                        ipynb_content.append(f"```python\n{cell.source}\n```")

                return md_header + "\n".join(ipynb_content) + "\n=== 该文件结束 ===\n"
            except ImportError:
                logger.warning(f"未安装nbformat，IPYNB文件{file_path}降级为JSON纯文本读取")
                with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                    content = json.dumps(json.load(f), indent=2, ensure_ascii=False)
                return md_header + f"\n```json\n{content}\n```\n" + "=== 该文件结束 ===\n"

        # 未支持的类型（降级处理）
        else:
            with open(file_path, "r", encoding=ENCODING, errors="ignore") as f:
                content = f.read()
            return md_header + f"\n{content}\n" + "=== 该文件结束 ===\n"

    except Exception as e:
        logger.error(f"转换失败：{file_path} | 错误：{str(e)}", exc_info=False)
        return md_header + f"\n【文件转换失败：{str(e)}】\n=== 该文件结束 ===\n"


def merge_files(filtered_files: Dict[str, List[Path]]) -> None:
    """
    模式2：合并文件为MD（按项目名+类型+分卷+日期后缀命名）
    """
    global OUTPUT_ROOT, PROJECT_NAME
    merge_dir = Path(OUTPUT_ROOT) / "merged_files"
    merge_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"\n开始合并文件到：{merge_dir}")
    ui_set_context(current_stage="合并输出")
    ui_update_stage("merge", status="进行中", detail="生成 docs/code 合并文件")

    # 先清理旧的合并结果，确保仅保留最新版本
    removed_merge_files = 0
    for old_md in merge_dir.glob("*.md"):
        try:
            old_md.unlink()
            removed_merge_files += 1
        except Exception as e:
            logger.error(f"清理旧合并文件失败：{old_md} | 错误：{str(e)}", exc_info=False)
    if removed_merge_files:
        logger.info(f"已清理旧合并文件：{removed_merge_files}个")

    # 新增：生成日期后缀（格式：yymmdd_hhmm）
    date_suffix = datetime.datetime.now().strftime("%y%m%d_%H%M")

    # 阈值转换：MB → 字节
    size_threshold = MERGE_SIZE_THRESHOLD_MB * 1024 * 1024

    # 遍历两类文件（文档/代码）分别合并
    for file_type, files in filtered_files.items():
        if not files:
            logger.info(f"无{file_type}类文件，跳过合并")
            continue

        logger.info(f"\n开始合并{file_type}类文件（共{len(files)}个）")
        # 生成文件清单（用于合并文件开头）
        file_list = [str(f.relative_to(SOURCE_DIR)) for f in files]
        list_content = f"# {PROJECT_NAME} - {file_type.upper()}类文件清单（共{len(file_list)}个）\n"
        for idx, file in enumerate(file_list, 1):
            list_content += f"{idx}. {file}\n"
        list_content += "\n--- 以下为文件内容（按清单顺序）---\n"

        # 初始化合并缓冲区
        merge_buffer = [list_content]
        current_size = len(list_content.encode(ENCODING))
        file_index = 1  # 分卷索引

        def process_one_file(file_path: Path) -> None:
            nonlocal current_size, file_index, merge_buffer
            md_content = convert_to_md(file_path)
            content_size = len(md_content.encode(ENCODING))

            if SPLIT_MERGED_FILES:
                if current_size + content_size > size_threshold and merge_buffer != [list_content]:
                    merge_file_name = f"{PROJECT_NAME}_{file_type}_{file_index}_{date_suffix}.md"
                    merge_file_path = merge_dir / merge_file_name
                    with open(merge_file_path, "w", encoding=ENCODING) as f:
                        f.write("".join(merge_buffer))
                    logger.info(
                        f"分卷{file_index}写入完成：{merge_file_path}（大小：{current_size / 1024 / 1024:.2f}MB）"
                    )
                    merge_buffer = [list_content]
                    current_size = len(list_content.encode(ENCODING))
                    file_index += 1

            merge_buffer.append(md_content)
            current_size += content_size

        # 逐个处理文件（进度条显示，避免刷屏）
        if DASHBOARD is not None and len(files) > 0:
            total = len(files)
            for idx, file_path in enumerate(files, 1):
                process_one_file(file_path)
                if idx % 10 == 0 or idx == total:
                    ui_update_stage("merge", completed=idx, total=total, detail=f"当前类型: {file_type}")
        elif RICH_AVAILABLE and len(files) > 0:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                TextColumn("{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task_id = progress.add_task(f"合并{file_type}文件", total=len(files))
                for file_path in files:
                    process_one_file(file_path)
                    progress.update(task_id, advance=1)
        else:
            for file_path in files:
                process_one_file(file_path)

        if merge_buffer:
            if SPLIT_MERGED_FILES:
                merge_file_name = f"{PROJECT_NAME}_{file_type}_{file_index}_{date_suffix}.md"
            else:
                merge_file_name = f"{PROJECT_NAME}_{file_type}_{date_suffix}.md"
            merge_file_path = merge_dir / merge_file_name
            with open(merge_file_path, "w", encoding=ENCODING) as f:
                f.write("".join(merge_buffer))
            logger.info(f"写入完成：{merge_file_path}（大小：{current_size / 1024 / 1024:.2f}MB）")
            ui_log(f"写入完成：{merge_file_name}")

    logger.info(f"\n所有文件合并完成 | 合并文件目录：{merge_dir}")
    ui_update_stage("merge", status="完成", detail="合并文件输出完成")


# ======================== 主函数（核心修复：logger重新配置逻辑+动态目录）========================
def main():
    """主函数：自动下载 → 筛选 → 复制 → 合并"""
    global SOURCE_DIR, logger, OUTPUT_ROOT, PROJECT_NAME, DASHBOARD

    try:
        # 步骤0：加载配置文件（实现与配置分离）
        load_config()

        # 步骤0：启动先检查Python与依赖环境
        ensure_runtime_environment()

        # 步骤1：获取用户输入的仓库名，自动下载并解压
        repo_name_input = input(
            f"请输入GitHub仓库名（格式：用户名/仓库名，默认：{DEFAULT_GITHUB_REPO}）："
        ).strip()
        repo_name = repo_name_input or DEFAULT_GITHUB_REPO
        logger.info(f"本次使用仓库：{repo_name}")

        # 按配置生成输出目录
        OUTPUT_ROOT = build_output_root(repo_name)
        output_root_path = Path(OUTPUT_ROOT)

        # 记录处理前输出目录数据
        before_total = calculate_dir_metrics(output_root_path)
        before_original = calculate_dir_metrics(output_root_path / "original_files")
        before_merged = calculate_dir_metrics(output_root_path / "merged_files")

        # 启动终端Dashboard（rich可用且配置启用）
        if RICH_AVAILABLE and TUI_ENABLED:
            DASHBOARD = TerminalDashboard(max_events=TUI_MAX_EVENTS)
            DASHBOARD.start()
            ui_set_context(repo_name=repo_name, output_dir=OUTPUT_ROOT, current_stage="准备中")
            ui_log("Dashboard 已启动")

        # 步骤2：提前创建输出根目录
        output_root_path.mkdir(parents=True, exist_ok=True)
        ui_set_context(output_dir=OUTPUT_ROOT)

        # 步骤3：重新配置日志到最终输出目录
        if logger is not None:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

        handlers = [logging.FileHandler(f"{OUTPUT_ROOT}/process.log", encoding=ENCODING)]
        if DASHBOARD is None:
            handlers.insert(0, logging.StreamHandler(sys.stdout))

        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s: %(message)s",
            handlers=handlers,
        )
        logger = logging.getLogger(__name__)

        ui_log("日志系统就绪")

        # 下载仓库并提取项目名（PROJECT_NAME在download_github_repo中赋值）
        SOURCE_DIR = download_github_repo(repo_name)

        # 步骤4：原有处理逻辑（完全保留）
        logger.info(f"源目录（下载解压后）：{SOURCE_DIR}")
        logger.info(f"输出根目录已创建：{OUTPUT_ROOT}")
        logger.info(f"当前处理项目名：{PROJECT_NAME}")
        ui_log(f"源目录：{SOURCE_DIR}")

        # 步骤5：筛选核心文件
        filtered_files = filter_core_files(SOURCE_DIR)

        # 步骤6：复制原始文件（保留结构）
        copy_original_files(filtered_files)

        # 步骤7：合并为MD文件
        merge_files(filtered_files)

        # 最终提示
        logger.info("\n==================== 处理完成 ====================")
        logger.info(f"原始文件目录：{Path(OUTPUT_ROOT) / 'original_files'}")
        logger.info(f"合并文件目录：{Path(OUTPUT_ROOT) / 'merged_files'}")
        logger.info(f"处理日志文件：{OUTPUT_ROOT}/process.log")
        logger.info(f"合并文件命名规则：{PROJECT_NAME}_{{类型}}_{{分卷}}_{{日期}}.md")
        logger.info("可将merged_files目录下的MD文件上传至Notebook LLM，original_files用于备份/核对")

        # 输出目录处理前后对比
        after_total = calculate_dir_metrics(output_root_path)
        after_original = calculate_dir_metrics(output_root_path / "original_files")
        after_merged = calculate_dir_metrics(output_root_path / "merged_files")

        logger.info(
            "目录对比[original_files] | "
            f"文件数: {before_original['files']} -> {after_original['files']} "
            f"(变化 {after_original['files'] - before_original['files']:+d}) | "
            f"大小: {format_bytes(before_original['bytes'])} -> {format_bytes(after_original['bytes'])} "
            f"(变化 {format_bytes(after_original['bytes'] - before_original['bytes'])})"
        )
        logger.info(
            "目录对比[merged_files] | "
            f"文件数: {before_merged['files']} -> {after_merged['files']} "
            f"(变化 {after_merged['files'] - before_merged['files']:+d}) | "
            f"大小: {format_bytes(before_merged['bytes'])} -> {format_bytes(after_merged['bytes'])} "
            f"(变化 {format_bytes(after_merged['bytes'] - before_merged['bytes'])})"
        )
        logger.info(
            "目录对比[输出总目录] | "
            f"文件数: {before_total['files']} -> {after_total['files']} "
            f"(变化 {after_total['files'] - before_total['files']:+d}) | "
            f"大小: {format_bytes(before_total['bytes'])} -> {format_bytes(after_total['bytes'])} "
            f"(变化 {format_bytes(after_total['bytes'] - before_total['bytes'])})"
        )
        ui_log(
            "输出目录对比完成："
            f"总文件 {before_total['files']} -> {after_total['files']}，"
            f"总大小 {format_bytes(before_total['bytes'])} -> {format_bytes(after_total['bytes'])}"
        )
        ui_set_context(current_stage="完成")
        ui_log("全部任务执行完成")

        # 清理临时日志目录
        shutil.rmtree(str(SCRIPT_DIR / "temp_log"), ignore_errors=True)
        # 清理临时解压目录
        shutil.rmtree(str(SCRIPT_DIR / "temp_github_repo"), ignore_errors=True)

    except KeyboardInterrupt:
        if logger is not None:
            logger.info("\n用户中断脚本执行")
        else:
            print("\n用户中断脚本执行")
        ui_set_context(current_stage="已中断")
        ui_log("用户中断执行")
        sys.exit(0)
    except Exception as e:
        if logger is not None:
            logger.error(f"脚本执行失败：{str(e)}", exc_info=True)
        else:
            print(f"脚本执行失败：{str(e)}")
        ui_set_context(current_stage="失败")
        ui_log(f"执行失败：{str(e)}")
        # 清理临时目录
        shutil.rmtree(str(SCRIPT_DIR / "temp_log"), ignore_errors=True)
        shutil.rmtree(str(SCRIPT_DIR / "temp_github_repo"), ignore_errors=True)
        sys.exit(1)
    finally:
        if DASHBOARD is not None:
            DASHBOARD.stop()
            DASHBOARD = None


if __name__ == "__main__":
    main()
