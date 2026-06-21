#!/usr/bin/env bash

# ============================================================
# API 自动化测试一键运行脚本
#
# 功能：
# 1. 清理旧的 Allure 结果
# 2. 执行 tests/api 下的接口测试
# 3. 生成 Allure 原始结果
# 4. 复制 Allure 环境配置文件
# 5. 生成 Allure HTML 报告
# ============================================================

set -e

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)

# Allure 原始结果目录
ALLURE_RESULTS_DIR="$PROJECT_ROOT/reports/allure-results"

# Allure HTML 报告目录
ALLURE_REPORT_DIR="$PROJECT_ROOT/reports/allure-report"

# Allure 配置文件目录
ALLURE_CONFIG_DIR="$PROJECT_ROOT/tests/allure"

echo "============================================"
echo "开始执行 API 自动化测试"
echo "项目路径: $PROJECT_ROOT"
echo "============================================"

cd "$PROJECT_ROOT"

echo "1. 清理旧的测试报告目录"
rm -rf "$ALLURE_RESULTS_DIR"
rm -rf "$ALLURE_REPORT_DIR"

mkdir -p "$ALLURE_RESULTS_DIR"

echo "2. 执行 API 自动化测试"
pytest tests/api -v \
  --alluredir="$ALLURE_RESULTS_DIR" \
  --clean-alluredir

echo "3. 复制 Allure 环境配置文件"

if [ -f "$ALLURE_CONFIG_DIR/environment.properties" ]; then
  cp "$ALLURE_CONFIG_DIR/environment.properties" "$ALLURE_RESULTS_DIR/environment.properties"
fi

if [ -f "$ALLURE_CONFIG_DIR/categories.json" ]; then
  cp "$ALLURE_CONFIG_DIR/categories.json" "$ALLURE_RESULTS_DIR/categories.json"
fi

if [ -f "$ALLURE_CONFIG_DIR/executor.json" ]; then
  cp "$ALLURE_CONFIG_DIR/executor.json" "$ALLURE_RESULTS_DIR/executor.json"
fi

echo "4. 生成 Allure HTML 报告"

# Allure 3 npm 版：
# - 不使用 --clean
# - 使用 --cwd 指定项目根目录
# - 使用 --output 指定报告输出目录
allure generate \
  --cwd "$PROJECT_ROOT" \
  --output "$ALLURE_REPORT_DIR"

echo "============================================"
echo "API 自动化测试执行完成"
echo "Allure 原始结果目录: $ALLURE_RESULTS_DIR"
echo "Allure HTML 报告目录: $ALLURE_REPORT_DIR"
echo ""
echo "查看报告请执行:"
echo "bash scripts/serve_allure_report.sh"
echo "============================================"