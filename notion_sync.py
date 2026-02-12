#!/usr/bin/env python3
"""
MEMORY.md → Notion Knowledge Base Sync

自动将本地OpenClaw内存文件同步到Notion知识库。
"""

import os
import re
import json
import hashlib
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import html

# 配置
NOTION_KEY_PATH = os.path.expanduser('~/.config/notion/api_key')
WORKSPACE = Path('/home/ubuntu/.openclaw/workspace')
MEMORY_DIR = WORKSPACE / 'memory'
MEMORY_FILE = WORKSPACE / 'MEMORY.md'

# Notion数据库ID (从环境变量读取，或在此处填写您的数据库ID)
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', 'YOUR_NOTION_DATABASE_ID_HERE')

# Notion属性限制
MAX_BODY_LENGTH = 2000
MAX_TITLE_LENGTH = 100
MAX_TAGS = 7

# 日志设置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class NotionClient:
    """简单的Notion API客户端"""

    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id

    def _curl_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """执行curl请求"""
        cmd = [
            "curl", "-s", "-X", method, endpoint,
            "-H", f"Authorization: Bearer {self.api_key}",
            "-H", "Notion-Version: 2025-09-03",
            "-H", "Content-Type: application/json",
        ]
        if data:
            cmd.extend(["-d", json.dumps(data)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error(f"JSON decode error: {result.stdout[:300]}")
            return None

    def create_page(self, properties: Dict, children: List[Dict] = None) -> Optional[str]:
        """创建新页面"""
        payload = {"parent": {"database_id": self.database_id}, "properties": properties}
        if children:
            payload["children"] = children

        resp = self._curl_request("POST", "https://api.notion.com/v1/pages", payload)
        if resp and resp.get("object") == "page":
            page_id = resp.get("id")
            logger.info(f"✅ Created page: {page_id}")
            return page_id
        else:
            logger.error(f"Failed to create page: {resp.get('message') if resp else 'No response'}")
            return None

    def update_page(self, page_id: str, properties: Dict = None) -> bool:
        """更新页面属性"""
        if not properties:
            return True

        payload = {"properties": properties}
        resp = self._curl_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}", payload)
        return resp and resp.get("object") == "page"

    def query_by_source_file(self, source_file: str) -> Optional[str]:
        """根据Source_File查找页面"""
        query = {
            "filter": {
                "property": "Source File",
                "rich_text": {"contains": source_file}
            }
        }
        resp = self._curl_request("POST", f"https://api.notion.com/v1/databases/{self.database_id}/query", query)
        if resp and resp.get("results"):
            return resp["results"][0].get("id")
        return None


class MemoryParser:
    """解析MEMORY.md和每日文件"""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.memory_dir = workspace / 'memory'

    def parse_memory_file(self) -> List[Dict]:
        """解析MEMORY.md"""
        entries = []
        memory_path = self.workspace / 'MEMORY.md'
        if not memory_path.exists():
            logger.warning(f"MEMORY.md not found")
            return entries

        content = memory_path.read_text()
        lines = content.split('\n')

        current_section = None
        current_entry = None
        entry_buffer = []

        for line in lines:
            if line.startswith('## '):
                if current_entry and entry_buffer:
                    current_entry['body'] = '\n'.join(entry_buffer).strip()
                    entries.append(current_entry)
                    entry_buffer = []

                section_title = line[3:].strip()
                if any(kw in section_title for kw in ['Standard', 'Protocol', 'Lesson', 'Framework']):
                    current_section = section_title
                else:
                    current_section = None
                continue

            if line.startswith('### ') and current_section:
                if current_entry and entry_buffer:
                    current_entry['body'] = '\n'.join(entry_buffer).strip()
                    entries.append(current_entry)
                    entry_buffer = []

                entry_title = line[4:].strip()
                current_entry = {
                    'title': entry_title,
                    'source': 'MEMORY.md',
                    'section': current_section,
                    'file': 'MEMORY.md'
                }
                continue

            if current_entry is not None:
                entry_buffer.append(line)

        if current_entry and entry_buffer:
            current_entry['body'] = '\n'.join(entry_buffer).strip()
            entries.append(current_entry)

        logger.info(f"Parsed {len(entries)} entries from MEMORY.md")
        return entries

    def parse_daily_files(self, days_back: int = 7) -> List[Dict]:
        """解析最近N天的memory文件"""
        entries = []
        today = datetime.now().date()

        for i in range(days_back):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            file_path = self.memory_dir / f'{date_str}.md'

            if not file_path.exists():
                continue

            content = file_path.read_text()
            lines = content.split('\n')

            current_section = None
            current_entry = None
            entry_buffer = []

            for line in lines:
                if line.startswith('## '):
                    if current_entry and entry_buffer:
                        current_entry['body'] = '\n'.join(entry_buffer).strip()
                        entries.append(current_entry)
                        entry_buffer = []

                    section_title = line[3:].strip()
                    if any(keyword in section_title.lower() for keyword in
                          ['research', 'finding', 'lesson', 'decision', 'insight', 'pattern', 'key takeaway', 'benchmark']):
                        current_section = section_title
                    else:
                        current_section = None
                    continue

                if line.startswith('### ') and current_section:
                    if current_entry and entry_buffer:
                        current_entry['body'] = '\n'.join(entry_buffer).strip()
                        entries.append(current_entry)
                        entry_buffer = []

                    entry_title = line[4:].strip()
                    current_entry = {
                        'title': entry_title,
                        'source': 'daily',
                        'file': f'{date_str}.md',
                        'date': date_str,
                        'section': current_section
                    }
                    continue

                if current_entry is not None:
                    entry_buffer.append(line)

            if current_entry and entry_buffer:
                current_entry['body'] = '\n'.join(entry_buffer).strip()
                entries.append(current_entry)

        logger.info(f"Parsed {len(entries)} knowledge entries from daily files (last {days_back} days)")
        return entries

    def extract_all_entries(self, days_back: int = 7) -> List[Dict]:
        """提取所有知识条目，去重"""
        all_entries = []
        all_entries.extend(self.parse_memory_file())
        all_entries.extend(self.parse_daily_files(days_back))

        # 去重（基于标题+内容哈希）
        seen = set()
        unique_entries = []
        for entry in all_entries:
            content_hash = hashlib.md5(
                f"{entry['title']}|{entry.get('date', '')}|{entry['body'][:200]}".encode()
            ).hexdigest()[:16]
            if content_hash not in seen:
                seen.add(content_hash)
                unique_entries.append(entry)

        logger.info(f"Total unique knowledge entries: {len(unique_entries)}")
        return unique_entries


class EntryClassifier:
    """分类和属性分配"""

    TYPE_KEYWORDS = {
        'Research': ['research', 'benchmark', 'analysis', 'comparison', 'technical deep dive', 'performance', 'detailed breakdown'],
        'Lesson': ['lesson', 'learned', 'mistake', 'error', 'issue', 'problem', 'fixed', 'resolved', 'blocker'],
        'Decision': ['decision', 'choose', 'selected', 'opted', 'concluded', 'determined', 'agreed', 'strategy'],
        'Pattern': ['pattern', 'trend', 'recurring', 'common', 'usually', 'typically', 'observation'],
        'Tutorial': ['how to', 'tutorial', 'guide', 'step', 'instruction', 'walkthrough', 'setup', 'configure'],
        'Reference': ['reference', 'cheatsheet', 'spec', 'specification', 'documentation', 'api', 'quick reference'],
        'Insight': ['insight', 'realized', 'noticed', 'observed', 'thought', 'idea', 'aha', 'epiphany'],
    }

    DOMAIN_KEYWORDS = {
        'AI Models': ['model', 'llm', 'gpt', 'claude', 'gemini', 'stepflash', 'deepseek', 'mimo', 'devstral', 'openrouter', 'free tier', 'notion'],
        'OpenClaw': ['openclaw', 'agent', 'workflow', 'skill', 'tool', 'automation', 'sync', 'database'],
        'Cost Optimization': ['cost', 'price', '$', 'budget', 'free', 'tier', 'routing', 'saving', 'optimization', 'value'],
        'Trading': ['trading', 'invest', 'stock', 'crypto', 'nft', 'web3', 'defi', 'bitcoin', 'ethereum'],
        'Learning': ['learn', 'study', 'japanese', 'language', 'course', 'tutorial', 'duolingo'],
        'Process': ['process', 'workflow', 'method', 'procedure', 'system', 'framework'],
    }

    CERTAINTY_PHRASES = {
        'Verified': ['proven', 'confirmed', 'tested', 'verified', 'measured', 'data shows', 'benchmark result'],
        'Likely': ['likely', 'probably', 'most likely', 'seems', 'appears', 'suggest'],
        'Speculative': ['maybe', 'might', 'could', 'possibly', 'hypothesis', 'guess', 'uncertain'],
        'Opinion': ['i think', 'believe', 'feel', 'in my view', 'personally', 'prefer']
    }

    IMPACT_INDICATORS = {
        'High': ['critical', 'important', 'must', 'essential', 'key', 'major', 'significant', 'game changer'],
        'Medium': ['relevant', 'useful', 'helpful', 'worth', 'good', 'beneficial'],
        'Low': ['minor', 'small', 'slight', 'marginal', 'nice to have'],
        'Negligible': ['negligible', 'tiny', 'minimal', 'barely', 'insignificant']
    }

    def classify_type(self, title: str, body: str) -> str:
        text = (title + ' ' + body).lower()
        for ctype, keywords in self.TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return ctype
        return 'Insight'

    def classify_domain(self, title: str, body: str) -> str:
        text = (title + ' ' + body).lower()
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return domain
        return 'General'

    def classify_certainty(self, body: str) -> str:
        text = body.lower()
        for certainty, phrases in self.CERTAINTY_PHRASES.items():
            if any(phrase in text for phrase in phrases):
                return certainty
        return 'Verified'

    def classify_impact(self, title: str, body: str) -> str:
        text = (title + ' ' + body).lower()
        for impact, indicators in self.IMPACT_INDICATORS.items():
            if any(ind in text for ind in indicators):
                return impact
        return 'Medium'

    def extract_tags(self, title: str, body: str, section: str) -> List[str]:
        tags = []
        text = (title + ' ' + body + ' ' + section).lower()

        keyword_map = {
            'AI': ['ai', 'artificial intelligence', 'ml', 'machine learning', 'model'],
            'OpenRouter': ['openrouter', 'router', 'provider', 'stepfun', 'moonshot', 'xiaomi', 'mistral'],
            'FreeTier': ['free', 'free tier', 'no cost'],
            'Benchmark': ['benchmark', 'test', 'score', 'performance', 'swe-bench', 'aime'],
            'Cost': ['cost', 'price', '$', 'pricing', 'budget', 'optimization'],
            'Automation': ['automation', 'auto', 'script', 'workflow', 'agent', 'tool'],
            'Coding': ['code', 'programming', 'development', 'swe', 'coding'],
            'Notion': ['notion', 'database', 'knowledge base', 'sync'],
            'Decision': ['decision', 'choose', 'selected', 'strategy'],
        }

        for tag, words in keyword_map.items():
            if any(w in text for w in words):
                tags.append(tag)

        return list(set(tags))[:MAX_TAGS]

    def classify(self, entry: Dict) -> Dict:
        title = entry.get('title', '')
        body = entry.get('body', '')

        meta = {
            'content_type': self.classify_type(title, body),
            'domain': self.classify_domain(title, body),
            'certainty': self.classify_certainty(body),
            'impact': self.classify_impact(title, body),
            'confidence_score': self._estimate_confidence(title, body, entry.get('source')),
            'tags': self.extract_tags(title, body, entry.get('section', '')),
            'source': entry.get('source', 'Manual'),
        }
        entry['metadata'] = meta
        return entry

    def _estimate_confidence(self, title: str, body: str, source: str) -> int:
        score = 7
        if source == 'MEMORY.md':
            score += 1
        if len(body) > 500:
            score += 1
        if any(w in body.lower() for w in ['data', 'benchmark', 'measured', 'tested']):
            score += 1
        return min(10, max(1, score))


class MarkdownToNotion:
    """将Markdown风格文本转换为Notion块"""

    def convert(self, text: str) -> List[Dict]:
        """转换文本为Notion块列表"""
        blocks = []
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if not line.strip():
                i += 1
                continue

            # 标题
            if line.startswith('# '):
                blocks.append(self._create_heading(1, line[2:]))
            elif line.startswith('## '):
                blocks.append(self._create_heading(2, line[3:]))
            elif line.startswith('### '):
                blocks.append(self._create_heading(3, line[4:]))
            # 无序列表
            elif line.startswith('- ') or line.startswith('* '):
                blocks.extend(self._parse_list(lines, i, '-'))
                i = self._skip_list(lines, i, '-')
                continue
            # 有序列表
            elif re.match(r'^\d+\. ', line):
                blocks.extend(self._parse_list(lines, i, 'numbered'))
                i = self._skip_list(lines, i, 'numbered')
                continue
            # 引用
            elif line.startswith('> '):
                blocks.append(self._create_quote(line[2:]))
            # 代码块
            elif line.startswith('```'):
                code_lines, new_i = self._parse_code_block(lines, i)
                lang = lines[i][3:].strip() if len(lines[i]) > 3 else ''
                blocks.append(self._create_code('\n'.join(code_lines), language=lang if lang else None))
                i = new_i
                continue
            # 分割线
            elif line.strip() in ['---', '***', '___']:
                blocks.append(self._create_divider())
            # 表格
            elif '|' in line and line.count('|') >= 3:
                table_text = line
                j = i + 1
                while j < len(lines) and '|' in lines[j]:
                    table_text += '\n' + lines[j]
                    j += 1
                blocks.append(self._create_code(table_text, language='markdown-table'))
                i = j
                continue
            # 普通段落
            else:
                blocks.append(self._create_paragraph(line))

            i += 1

        return blocks

    def _create_heading(self, level: int, text: str) -> Dict:
        text = text[:2000]  # 安全截断
        return {"object": "block", "type": f"heading_{level}", f"heading_{level}": {"rich_text": [{"text": {"content": text}}]}}

    def _create_paragraph(self, text: str) -> Dict:
        text = text[:2000]
        return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": text}}]}}

    def _create_list_item(self, text: str) -> Dict:
        text = text[:2000]
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": text}}]}}

    def _parse_list(self, lines: List[str], start: int, list_type: str) -> List[Dict]:
        blocks = []
        i = start
        while i < len(lines):
            line = lines[i].rstrip()
            if not line.strip():
                i += 1
                continue
            is_match = False
            if list_type == '-' and line.startswith('- '):
                is_match = True
                prefix = '- '
            elif list_type == 'numbered' and re.match(r'^\d+\. ', line):
                is_match = True
                prefix = re.match(r'^\d+\. ', line).group(0)
            else:
                break

            if is_match:
                content = line[len(prefix):].strip()
                blocks.append(self._create_list_item(content))
            i += 1
        return blocks

    def _skip_list(self, lines: List[str], start: int, list_type: str) -> int:
        i = start
        while i < len(lines):
            line = lines[i].rstrip()
            if not line.strip():
                i += 1
                continue

            is_match = False
            if list_type == '-' and line.startswith('- '):
                is_match = True
            elif list_type == 'numbered' and re.match(r'^\d+\. ', line):
                is_match = True

            if is_match:
                i += 1
            else:
                break
        return i

    def _parse_code_block(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        code_lines = []
        i = start + 1
        while i < len(lines):
            if lines[i].strip() == '```':
                return code_lines, i + 1
            code_lines.append(lines[i].rstrip())
            i += 1
        return code_lines, i

    def _create_code(self, code: str, language: str = None) -> Dict:
        code = code[:2000]
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"text": {"content": code}}],
                "caption": [],
                "language": language if language else "plain text"
            }
        }

    def _create_quote(self, text: str) -> Dict:
        text = text[:2000]
        return {"object": "block", "type": "quote", "quote": {"rich_text": [{"text": {"content": text}}]}}

    def _create_divider(self) -> Dict:
        return {"object": "block", "type": "divider", "divider": {}}


class SyncOrchestrator:
    """同步编排器"""

    def __init__(self, notion_client: NotionClient, memory_parser: MemoryParser, classifier: EntryClassifier, converter: MarkdownToNotion):
        self.notion = notion_client
        self.parser = memory_parser
        self.classifier = classifier
        self.converter = converter
        self.sync_log_path = WORKSPACE / 'memory' / 'sync-log.md'

    def log_action(self, action: str, details: str):
        """记录同步操作"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"- {timestamp}: {action} - {details}\n"
        with open(self.sync_log_path, 'a') as f:
            f.write(log_entry)
        logger.info(f"📝 {action}: {details}")

    def _truncate_text(self, text: str, max_len: int) -> str:
        """智能截断文本，尽量在句子边界截断"""
        if len(text) <= max_len:
            return text
        # 尝试在句子边界截断
        for sep in ['\n\n', '. ', '! ', '? ', '; ']:
            idx = text.rfind(sep, 0, max_len)
            if idx > max_len * 0.5:  # 至少保留50%才用句子截断
                return text[:idx+1].strip()
        # 否则硬截断并加...
        return text[:max_len-3].strip() + '...'

    def process_entry(self, entry: Dict, dry_run: bool = False) -> Optional[str]:
        """处理单个条目"""
        entry = self.classifier.classify(entry)
        meta = entry['metadata']
        source_file = entry.get('file', 'unknown')
        existing_page_id = self.notion.query_by_source_file(source_file)

        # 构建属性 - 使用空格名称
        properties = {
            "Name": {"title": [{"text": {"content": entry['title'][:MAX_TITLE_LENGTH]}}]},
            "Content Type": {"select": {"name": meta['content_type']}},
            "Domain": {"select": {"name": meta['domain']}},
            "Certainty": {"select": {"name": meta['certainty']}},
            "Source": {"select": {"name": meta['source']}},
            "Confidence Score": {"number": meta['confidence_score']},
            "Impact": {"select": {"name": meta['impact']}},
            "Source File": {"rich_text": [{"text": {"content": source_file}}]}
        }

        if meta['tags']:
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in meta['tags']]}

        body_content = entry.get('body', '')
        if body_content and len(body_content) > 50:
            # Body属性（长度限制2000字符）
            truncated_body = self._truncate_text(body_content, MAX_BODY_LENGTH)
            properties["Body"] = {"rich_text": [{"text": {"content": truncated_body}}]}

        # 转换为Notion块用于页面内容
        children = None
        if body_content and len(body_content) > 50:
            children = self.converter.convert(body_content)

        if dry_run:
            self.log_action("DRY-RUN", f"Would {'update' if existing_page_id else 'create'}: {entry['title']}")
            logger.info(f"[DRY-RUN] Title: {entry['title']}")
            logger.info(f"  Type: {meta['content_type']}, Domain: {meta['domain']}")
            logger.info(f"  Confidence: {meta['confidence_score']}, Impact: {meta['impact']}")
            logger.info(f"  Tags: {meta['tags']}")
            logger.info(f"  Body length: {len(body_content)} (truncated to {MAX_BODY_LENGTH})")
            logger.info(f"  Children: {len(children) if children else 0} blocks")
            return None

        if existing_page_id:
            success = self.notion.update_page(existing_page_id, properties=properties)
            if success:
                self.log_action("UPDATED", f"{entry['title']} (page: {existing_page_id})")
                return existing_page_id
            else:
                self.log_action("UPDATE_FAILED", f"{entry['title']}")
                return None
        else:
            page_id = self.notion.create_page(properties, children=children)
            if page_id:
                self.log_action("CREATED", f"{entry['title']} (page: {page_id})")
            else:
                self.log_action("CREATE_FAILED", f"{entry['title']}")
            return page_id

    def sync(self, days_back: int = 7, dry_run: bool = False, limit: int = None):
        logger.info("=" * 60)
        logger.info(f"Starting sync: days_back={days_back}, dry_run={dry_run}, limit={limit}")
        logger.info("=" * 60)

        entries = self.parser.extract_all_entries(days_back)
        if limit:
            entries = entries[:limit]

        logger.info(f"Processing {len(entries)} entries...")

        stats = {'created': 0, 'updated': 0, 'failed': 0}
        for i, entry in enumerate(entries, 1):
            logger.info(f"[{i}/{len(entries)}] Processing: {entry.get('title', 'Unknown')}")
            try:
                page_id = self.process_entry(entry, dry_run)
                if page_id:
                    stats['created' if not self.notion.query_by_source_file(entry['file']) else 'updated'] += 1
                else:
                    stats['failed'] += 1
            except Exception as e:
                logger.error(f"Error processing entry: {e}", exc_info=True)
                stats['failed'] += 1

        logger.info("=" * 60)
        logger.info("Sync completed!")
        logger.info(f"  Created: {stats['created']}")
        logger.info(f"  Updated: {stats['updated']}")
        logger.info(f"  Failed:  {stats['failed']}")
        logger.info("=" * 60)


def main():
    parser_cli = argparse.ArgumentParser(description='Sync MEMORY.md to Notion Knowledge Base')
    parser_cli.add_argument('--dry-run', action='store_true', help='Preview changes without making them')
    parser_cli.add_argument('--verbose', action='store_true', help='Show debug logs')
    parser_cli.add_argument('--since', type=str, help='Only sync entries since YYYY-MM-DD')
    parser_cli.add_argument('--limit', type=int, help='Limit number of entries to process')
    args = parser_cli.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not os.path.exists(NOTION_KEY_PATH):
        logger.error(f"Notion API key not found at {NOTION_KEY_PATH}")
        return 1

    with open(NOTION_KEY_PATH) as f:
        api_key = f.read().strip()

    notion = NotionClient(api_key, NOTION_DATABASE_ID)
    memory_parser = MemoryParser(WORKSPACE)
    classifier = EntryClassifier()
    converter = MarkdownToNotion()

    days_back = 7
    if args.since:
        try:
            since_date = datetime.strptime(args.since, '%Y-%m-%d').date()
            days_back = (datetime.now().date() - since_date).days + 1
        except ValueError:
            logger.error("Invalid date format for --since. Use YYYY-MM-DD")
            return 1

    orchestrator = SyncOrchestrator(notion, memory_parser, classifier, converter)
    orchestrator.sync(days_back=days_back, dry_run=args.dry_run, limit=args.limit)

    return 0


if __name__ == '__main__':
    exit(main())
