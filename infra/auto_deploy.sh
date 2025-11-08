#!/usr/bin/env bash
set -euo pipefail

# === Конфигурация по умолчанию ===
: "${COOLIFY_URL:=https://app.coolify.io/api/v1}"
: "${APP_TAG:=quizbee}"                 # Тег приложений в Coolify ?tags=
: "${REMOTE:=origin}"                   # Гит-ремоут
: "${MAIN_BRANCH:=main}"                # Основная ветка

# === Аргументы ===
# 1) bump: major | minor | patch | vX.Y.Z (явное значение)
# 2) (необязательно) --no-deploy | --dry-run
BUMP="${1:-}"
EXTRA="${2:-}"

if [[ -z "${COOLIFY_TOKEN:-}" ]]; then
  echo "❌ Установите COOLIFY_TOKEN в окружении"
  exit 1
fi

if [[ -z "$BUMP" ]]; then
  echo "❌ Usage: COOLIFY_TOKEN=... $0 <major|minor|patch|vX.Y.Z> [--no-deploy|--dry-run]"
  exit 1
fi

NO_DEPLOY=false
DRY=false
case "${EXTRA:-}" in
  --no-deploy) NO_DEPLOY=true ;;
  --dry-run)   DRY=true; NO_DEPLOY=true ;;
  "" ) ;;
  *) echo "❌ Неизвестный флаг: ${EXTRA}"; exit 1 ;;
esac

# === Утилиты ===
ver_normalize() { # strip leading 'v'
  echo "${1#v}"
}

bump_version() { # $1=current vX.Y.Z  $2=major|minor|patch
  local cur raw major minor patch
  raw="$(ver_normalize "$1")"
  IFS='.' read -r major minor patch <<<"$raw"
  case "$2" in
    major) echo "v$((major+1)).0.0" ;;
    minor) echo "v${major}.$((minor+1)).0" ;;
    patch) echo "v${major}.${minor}.$((patch+1))" ;;
    *) echo "❌ неизвестный тип bump: $2" >&2; return 1 ;;
  esac
}

latest_tag_on_main() {
  # Берём последний по версии тег 'v*', достижимый из origin/main
  git fetch --tags --quiet "$REMOTE" "+refs/heads/${MAIN_BRANCH}:refs/remotes/${REMOTE}/${MAIN_BRANCH}"
  git tag --list 'v*' --merged "${REMOTE}/${MAIN_BRANCH}" | sort -V | tail -n1
}

head_of_main_commit() {
  git rev-parse "${REMOTE}/${MAIN_BRANCH}"
}

create_and_push_tag() { # $1=new_tag  $2=commit
  local tag="$1" commit="$2"
  if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
    echo "✅ Тег ${tag} уже существует (пропускаю создание)"
  else
    if [[ "$DRY" == true ]]; then
      echo "🧪 DRY-RUN: git tag -a ${tag} ${commit} -m \"Release ${tag}\""
    else
      git tag -a "${tag}" "${commit}" -m "Release ${tag}"
      git push "$REMOTE" "${tag}"
      echo "🏷️  Создан и отправлен тег ${tag} → ${REMOTE}"
    fi
  fi
}

deploy_coolify_by_tag() { # $1=commit_sha
  local commit="$1"
  echo "🔍 Получаю список приложений с тегом '${APP_TAG}'..."
  local APPS_JSON
  APPS_JSON=$(curl -sS -H "Authorization: Bearer $COOLIFY_TOKEN" \
    "$COOLIFY_URL/applications?tags=$APP_TAG")

  local APP_UUIDS
  APP_UUIDS=$(echo "$APPS_JSON" | jq -r '.[].uuid')

  if [[ -z "$APP_UUIDS" ]]; then
    echo "❌ Приложения с тегом '$APP_TAG' не найдены"
    exit 1
  fi

  for UUID in $APP_UUIDS; do
    echo "🔧 Фиксирую commit SHA для app ${UUID} → ${commit}"
    curl -sS -X PATCH "$COOLIFY_URL/applications/$UUID" \
      -H "Authorization: Bearer $COOLIFY_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"git_commit_sha\":\"$commit\",\"instant_deploy\":false}" >/dev/null
  done

  echo "🚀 Тригерю деплой для всех '$APP_TAG'..."
  curl -sS -H "Authorization: Bearer $COOLIFY_TOKEN" \
    "$COOLIFY_URL/deploy?tag=$APP_TAG&force=true" >/dev/null

  echo "✅ Deployment triggered successfully!"
}

# === Основной поток ===
git fetch --tags --quiet "$REMOTE"

LATEST_TAG="$(latest_tag_on_main || true)"
if [[ -z "$LATEST_TAG" ]]; then
  LATEST_TAG="v0.0.0"  # стартовая точка, если тегов нет
fi

# Проверяем, является ли BUMP конкретным тегом версии (vX.Y.Z)
if [[ "$BUMP" =~ ^v[0-9]+\. ]]; then
  # Проверяем полный формат vX.Y.Z
  if [[ "$BUMP" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    NEW_TAG="$BUMP"
    echo "ℹ️  Используется явно указанный тег: ${NEW_TAG}"
  else
    echo "❌ Неверный формат версии: ${BUMP}. Ожидается vX.Y.Z (например, v0.5.1)"
    exit 1
  fi
else
  # Обрабатываем bump типы (major|minor|patch)
  case "$BUMP" in
    major|minor|patch) NEW_TAG="$(bump_version "$LATEST_TAG" "$BUMP")" ;;
    *) echo "❌ Укажите major|minor|patch или явный vX.Y.Z (например, v0.5.1)"; exit 1 ;;
  esac
fi

MAIN_COMMIT="$(head_of_main_commit)"
echo "ℹ️  Последний тег на ${REMOTE}/${MAIN_BRANCH}: ${LATEST_TAG}"
echo "ℹ️  Новый релизный тег: ${NEW_TAG}"
echo "ℹ️  Коммит для тега: ${MAIN_COMMIT}"

create_and_push_tag "$NEW_TAG" "$MAIN_COMMIT"

if [[ "$NO_DEPLOY" == true ]]; then
  echo "ℹ️  Деплой отключён флагом --no-deploy${DRY:+ (DRY-RUN)}"
  exit 0
fi

# Деплой этого коммита в Coolify
deploy_coolify_by_tag "$MAIN_COMMIT"
