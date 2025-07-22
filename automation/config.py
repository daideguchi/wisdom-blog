"""
設定ファイル
カスタマイズ可能な設定をここで管理します
"""

import os

# 基本パス設定
OBSIDIAN_VAULT_PATH = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
PROJECT_ROOT = "/Users/dd/Desktop/1_dev/post_tool"

# 記事生成設定
ARTICLE_GENERATION_CONFIG = {
    "min_log_entries": 5,           # 最低5つのログで記事生成
    "generation_interval": "daily",  # 毎日記事生成チェック 
    "article_style": "technical",   # 技術記事スタイル
    "target_length": 800,           # 800文字程度
    "include_code": True,           # コードブロック含む
    "auto_publish": False,          # 自動投稿OFF（手動確認推奨）
    "emoji_style": "tech"           # 技術系絵文字を優先
}

# 監視対象設定
MONITORING_CONFIG = {
    "watch_folders": [
        "/Users/dd/Desktop/1_dev/post_tool",    # 現在のプロジェクト
        "/Users/dd/Desktop/1_dev",               # 開発フォルダ
        "/Users/dd/Desktop/dev",                 # 他の開発フォルダ
        "/Users/dd/projects"                     # プロジェクトフォルダ
    ],
    "git_repos": True,              # Git操作を監視
    "terminal_logs": False,         # ターミナル履歴監視（重いのでデフォルトOFF）
    "error_logs": True,             # エラーログ監視
    "file_extensions": [            # 監視対象の拡張子
        ".py", ".js", ".ts", ".tsx", ".jsx", 
        ".vue", ".go", ".rs", ".java", ".cpp",
        ".html", ".css", ".scss", ".md"
    ]
}

# AI設定
AI_CONFIG = {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 3000,
    "temperature": 0.7,
    "api_key_env": "ANTHROPIC_API_KEY"
}

# Zenn設定
ZENN_CONFIG = {
    "auto_publish": False,          # 自動投稿（要注意）
    "default_type": "tech",         # デフォルトタイプ
    "default_published": False,     # デフォルトで非公開
    "topics_limit": 5              # トピック数上限
}

# ブログ設定
BLOG_CONFIG = {
    "build_command": "npm run astro:build",
    "deploy_command": "vercel --prod",
    "auto_deploy": False           # 自動デプロイ
}

# セキュリティ設定
SECURITY_CONFIG = {
    "exclude_patterns": [          # 除外パターン
        "password", "secret", "token", "key", 
        "api_key", "private", "credential"
    ],
    "sanitize_logs": True,         # ログのサニタイズ
    "max_file_size": 1024 * 1024,  # 1MBまで
}

# ログレベル設定
LOGGING_CONFIG = {
    "level": "INFO",               # DEBUG, INFO, WARNING, ERROR
    "save_logs": True,             # ログファイル保存
    "console_output": True         # コンソール出力
}

def get_config(section=None):
    """設定を取得"""
    configs = {
        "article": ARTICLE_GENERATION_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "ai": AI_CONFIG,
        "zenn": ZENN_CONFIG,
        "blog": BLOG_CONFIG,
        "security": SECURITY_CONFIG,
        "logging": LOGGING_CONFIG
    }
    
    if section:
        return configs.get(section, {})
    return configs

def update_config(section, key, value):
    """設定を更新（実行時）"""
    configs = get_config()
    if section in configs and key in configs[section]:
        configs[section][key] = value
        print(f"設定更新: {section}.{key} = {value}")
        return True
    return False