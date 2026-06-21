# ============================================================
# Allure 报告查看脚本
#
# 功能：
# 启动本地 Allure 服务并打开测试报告
# ============================================================

set -e

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)

# Allure HTML 报告目录
ALLURE_REPORT_DIR="$PROJECT_ROOT/reports/allure-report"

echo "============================================"
echo "启动 Allure 测试报告"
echo "报告路径: $ALLURE_REPORT_DIR"
echo "============================================"

cd "$PROJECT_ROOT"

if [ ! -d "$ALLURE_REPORT_DIR" ]; then
  echo "未找到 Allure HTML 报告目录，请先执行："
  echo "bash scripts/run_api_tests.sh"
  exit 1
fi

allure open "$ALLURE_REPORT_DIR"