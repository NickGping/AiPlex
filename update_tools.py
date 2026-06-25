#!/usr/bin/env python3
"""
AI工具箱 — 工具数据自动更新脚本
用法: python3 update_tools.py [--check] [--update]

模式:
  --check   仅检查工具链接是否可达，报告状态
  --update  检查 + 更新 tools.json（后续可扩展自动拉取新工具）
  (默认)    使用 Hermes Agent 分析并建议新增工具

配合 Hermes cronjob 可实现每日自动巡检。
"""
import json, sys, time, urllib.request, urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent
TOOLS_JSON = BASE_DIR / "tools.json"
HTML_FILE = BASE_DIR / "index.html"

USER_AGENT = "AIToolbox-Updater/2.0 (https://nickgping.github.io/aitoolbox/)"

def load_tools():
    with open(TOOLS_JSON) as f:
        return json.load(f)

def save_tools(data):
    with open(TOOLS_JSON, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_url(url, timeout=8):
    """Check if a URL is reachable, returns (status_code, error_message)"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"连接失败: {e.reason}"
    except Exception as e:
        return None, str(e)

def check_all():
    """Check all tool links and report status"""
    data = load_tools()
    total = data['total']
    ok = 0
    failed = []
    
    print(f"🔍 巡检 {total} 个工具链接...\n")
    
    for i, tool in enumerate(data['tools'], 1):
        name = tool['name']
        url = tool['link']
        print(f"  [{i}/{total}] {name:20s} ", end='', flush=True)
        
        status, err = check_url(url)
        if status and 200 <= status < 400:
            print(f"✅ {status}")
            ok += 1
        else:
            print(f"❌ {err}")
            failed.append({'name': name, 'url': url, 'error': err})
        
        time.sleep(0.5)  # Be polite
    
    print(f"\n📊 结果: {ok}/{total} 可达")
    if failed:
        print(f"⚠️  {len(failed)} 个链接异常:")
        for f in failed:
            print(f"    - {f['name']}: {f['url']} ({f['error']})")
    
    return ok, failed

def update_json():
    """Update tools.json timestamp and sync count"""
    data = load_tools()
    data['updated'] = time.strftime('%Y-%m-%d')
    data['total'] = len(data['tools'])
    save_tools(data)
    print(f"✅ tools.json 已更新 — {data['total']} 个工具, {data['updated']}")

if __name__ == '__main__':
    if '--check' in sys.argv:
        ok, failed = check_all()
        sys.exit(1 if failed else 0)
    elif '--update' in sys.argv:
        update_json()
        ok, failed = check_all()
        sys.exit(1 if failed else 0)
    else:
        print("AI工具箱 — 工具数据管理")
        print(f"  当前: {load_tools()['total']} 个工具, 更新于 {load_tools()['updated']}")
        print()
        print("用法:")
        print("  python3 update_tools.py --check    # 巡检所有链接")
        print("  python3 update_tools.py --update   # 巡检 + 更新时间戳")
        print()
        print("配合 Hermes cronjob 自动运行:")
        print("  hermes cronjob create --prompt '跑 cd /mnt/c/Users/nickg/nick-website && python3 update_tools.py --update' --schedule '0 9 * * *'")
