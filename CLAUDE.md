# CLAUDE.md - WISDOM プロジェクト専用設定

## プロジェクト識別
**プロジェクト名**: post_tool (WISDOM)
**説明**: 開発ログ自動記事化ツール - AI拡張知識管理システム
**ステータス**: active

## 📦 モジュール継承
@import ../../config/claude_modules/projects/common_inheritance.md
@import ../../config/claude_modules/projects/web_stack.md
@import ../../config/claude_modules/projects/ai_integration.md

## 🎯 プロジェクト固有設定

### プロジェクト固有ルール
1. **Single Source of Truth**: Gitリポジトリが唯一の情報源
2. **自動化最優先**: 手動作業の完全排除を目指す
3. **知識統合**: 既存のObsidian Vaultとの完全統合
4. **品質重視**: AI生成コンテンツの品質管理徹底

### 追加技術スタック
- Astro（静的サイト生成）
- Python 3.8+（自動化スクリプト）
- Zenn CLI + Zenn Connect
- Obsidian Vault統合

### ツェッテルカステン原則
- **原子性**: 一つのノート、一つのアイデア
- **連結性**: すべての知識を相互連結
- **継続性**: 知識の継続的な蓄積と進化
- **創発性**: 新しい洞察の自然な発生

### コンテンツKPI
- 週間記事生成数: 目標3-5記事
- AI生成コンテンツ品質スコア: 80%以上
- SEO検索順位: 上位50位以内の記事率60%

### 知識管理KPI
- ノート間リンク密度: 平均3リンク/ノート
- 知識発見率: 月間10個以上の新しい関連性
- 活用率: 既存ノートの参照頻度20%向上

### 専用AI役割
- **CONTENT_ANALYZER**: Git・ログ分析専門
- **KNOWLEDGE_CURATOR**: 知識統合・リンク生成
- **QUALITY_CONTROLLER**: コンテンツ品質管理

### Obsidian統合パス
```
/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents/
├── 00_POST_TOOL_Integration/    # 統合フォルダ
│   ├── Automated_Insights/      # AI生成ノート
│   ├── Git_Analysis/           # Git分析結果
│   └── System_Logs/            # システムログ分析
```

### プロジェクト固有チェック
```bash
# Obsidian統合確認
python obsidian_integration_config.py --check

# 自動化システム確認
npm run system:health-check
```

### 自動化Cron Jobs
```bash
# 5分毎: ログファイル監視
*/5 * * * * python automation/dev_log_watcher.py

# 1時間毎: システムヘルスチェック
0 * * * * python automation/system_health_monitor.py

# 日次: Obsidian統合同期
0 6 * * * python automation/obsidian_sync.py
```

---
**更新日**: 2025-07-23 | **バージョン**: 2.0 (Modular)