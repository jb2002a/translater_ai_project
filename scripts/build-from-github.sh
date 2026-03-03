#!/bin/bash
# GitHub에서 최신 코드를 받아 Docker 이미지를 빌드합니다.
# EC2 등에서 로컬 디렉터리가 예전 코드일 때 사용하세요.
#
# 사용법 (EC2에서 어느 디렉터리에서든 실행 가능):
#   curl -sSL https://raw.githubusercontent.com/jb2002a/translater_ai_project/main/scripts/build-from-github.sh | bash
#   또는 프로젝트에서: bash scripts/build-from-github.sh
#
# 환경 변수: REPO_URL, GITHUB_BRANCH, IMAGE_NAME, BUILD_DIR

set -e

REPO_URL="${REPO_URL:-https://github.com/jb2002a/translater_ai_project.git}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"
IMAGE_NAME="${IMAGE_NAME:-trans-ai-app}"
# EC2에서 로컬 프로젝트와 분리된 경로에 클론 (어디서 실행해도 동일하게 동작)
BUILD_DIR="${BUILD_DIR:-$HOME/translater_ai_project_from_git}"

echo "=== GitHub에서 이미지 빌드 ==="
echo "  REPO_URL=$REPO_URL"
echo "  GITHUB_BRANCH=$GITHUB_BRANCH"
echo "  IMAGE_NAME=$IMAGE_NAME"
echo "  BUILD_DIR=$BUILD_DIR"
echo ""

if [ -d "$BUILD_DIR" ]; then
  echo "기존 빌드 디렉터리 갱신: $BUILD_DIR"
  (cd "$BUILD_DIR" && git fetch origin && git checkout "$GITHUB_BRANCH" && git pull origin "$GITHUB_BRANCH" || true)
else
  echo "클론: $REPO_URL (브랜치: $GITHUB_BRANCH) -> $BUILD_DIR"
  git clone --branch "$GITHUB_BRANCH" --depth 1 "$REPO_URL" "$BUILD_DIR"
fi

echo ""
echo "Docker 이미지 빌드 (캐시 없이): $IMAGE_NAME"
docker build --no-cache -t "$IMAGE_NAME" "$BUILD_DIR"

echo ""
echo "빌드 완료. 이미지 확인:"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}"

echo ""
echo "컨테이너 안 app.py에 새 업로드 API 포함 여부:"
docker run --rm "$IMAGE_NAME" grep -c "api/upload-pdf" /app/app.py || true

echo ""
echo "다음으로 기존 컨테이너를 끄고 새 이미지로 실행하세요:"
echo "  docker stop trans-ai-service 2>/dev/null; docker rm trans-ai-service 2>/dev/null"
echo "  docker run -d --name trans-ai-service -p 8080:8080 $IMAGE_NAME"
