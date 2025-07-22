#!/usr/bin/env python3
"""
セットアップチェックスクリプト
必要な環境が整っているかチェックします
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_packages():
    """必要なPythonパッケージをチェック"""
    required_packages = [
        'anthropic',
        'watchdog', 
        'python-frontmatter'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ 不足パッケージ: {', '.join(missing)}")
        print("インストールコマンド:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_api_key():
    """APIキーをチェック"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ ANTHROPIC_API_KEY")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY が設定されていません")
        print("設定方法:")
        print("export ANTHROPIC_API_KEY='your_api_key_here'")
        print("または .env ファイルに追加")
        return False

def check_folders():
    """必要なフォルダをチェック・作成"""
    obsidian_path = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    required_folders = [
        os.path.join(obsidian_path, "01_Dev_Logs"),
        os.path.join(obsidian_path, "02_Generated_Articles"),
        os.path.join(obsidian_path, "03_Published_Content"),
        "/Users/dd/Desktop/1_dev/post_tool/articles",
        "/Users/dd/Desktop/1_dev/post_tool/automation"
    ]
    
    all_ok = True
    for folder in required_folders:
        if os.path.exists(folder):
            print(f"✅ {folder}")
        else:
            try:
                os.makedirs(folder, exist_ok=True)
                print(f"📁 作成: {folder}")
            except Exception as e:
                print(f"❌ 作成失敗: {folder} - {e}")
                all_ok = False
    
    return all_ok

def check_git():
    """Git設定をチェック"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("❌ Git がインストールされていません")
        return False

def check_node():
    """Node.js設定をチェック"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("❌ Node.js がインストールされていません")
        return False

def create_env_file():
    """.envファイルのサンプルを作成"""
    env_path = "/Users/dd/Desktop/1_dev/post_tool/.env"
    if not os.path.exists(env_path):
        env_content = """# POST TOOL 環境変数設定

# Claude API Key (必須)
ANTHROPIC_API_KEY=your_claude_api_key_here

# Vercel設定 (ブログ自動デプロイ用)
VERCEL_TOKEN=your_vercel_token_here
VERCEL_ORG_ID=your_org_id_here  
VERCEL_PROJECT_ID=your_project_id_here

# 開発モード
DEBUG=true
"""
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"📄 .envファイルを作成: {env_path}")
        print("必要な値を入力してください")

def create_sample_log():
    """サンプルログファイルを作成"""
    obsidian_path = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    log_path = os.path.join(obsidian_path, "01_Dev_Logs", "sample_dev_log.json")
    
    sample_logs = [
        {
            "timestamp": "2025-01-22T15:30:00",
            "type": "file_modified", 
            "message": "ファイル編集: main.py",
            "details": {"file_path": "main.py", "extension": ".py"}
        },
        {
            "timestamp": "2025-01-22T15:45:00",
            "type": "git_commit",
            "message": "新しいコミット: React useEffect最適化",
            "details": {"hash": "abc123", "message": "React useEffect最適化"}
        },
        {
            "timestamp": "2025-01-22T16:00:00",
            "type": "file_modified",
            "message": "ファイル編集: components.tsx", 
            "details": {"file_path": "components.tsx", "extension": ".tsx"}
        }
    ]
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(sample_logs, f, ensure_ascii=False, indent=2)
    
    print(f"📝 サンプルログを作成: {log_path}")

def show_usage():
    """使用方法を表示"""
    print("\n🚀 使用方法:")
    print("1. 監視開始:     python automation/dev_log_watcher.py")  
    print("2. 記事生成:     python automation/article_generator.py")
    print("3. 設定確認:     python automation/setup_check.py")
    print("\n📚 詳細な使い方:")
    print("PROJECT_MASTER_BLUEPRINT.md を確認してください")

def main():
    print("🔍 POST TOOL セットアップチェック\n")
    
    checks = [
        ("Pythonパッケージ", check_python_packages),
        ("APIキー", check_api_key),
        ("フォルダ構造", check_folders),
        ("Git", check_git),
        ("Node.js", check_node)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}をチェック中...")
        result = check_func()
        results.append(result)
    
    print(f"\n{'='*50}")
    
    if all(results):
        print("🎉 セットアップ完了！全ての要件を満たしています")
        create_sample_log()
        show_usage()
    else:
        print("⚠️  一部の要件が不足しています")
        print("上記のエラーを修正してから再実行してください")
    
    # .envファイル作成
    create_env_file()

if __name__ == "__main__":
    main()