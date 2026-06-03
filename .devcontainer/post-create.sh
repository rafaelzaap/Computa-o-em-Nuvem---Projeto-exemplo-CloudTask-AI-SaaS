#!/usr/bin/env bash
# =============================================================================
# post-create.sh — roda UMA vez, após o devcontainer ser criado.
# -----------------------------------------------------------------------------
# Versão Semana 1: instala APENAS o que é necessário para a base do projeto
# (zsh plugins, .zshrc, ajustes git, /commandhistory). Sem AWS/k8s — esses
# entram em semanas posteriores.
#
# Roda como `appuser` (não-root) com sudo NOPASSWD habilitado no target dev
# do Dockerfile (necessário para criar /commandhistory).
# =============================================================================
# NÃO usamos `set -e`: se uma instalação falhar (ex.: sem rede no primeiro
# build), avisamos mas NÃO abortamos a criação do container.
set -uo pipefail

echo "==> [post-create] Criando pasta de histórico do zsh (volume persistente)..."
# /commandhistory é o destino do volume nomeado cloudtask-zsh-history
# (ver devcontainer.json). O zsh salva o histórico ali para sobreviver a
# rebuilds do container.
sudo mkdir -p /commandhistory
sudo chown -R appuser:appuser /commandhistory || true

echo "==> [post-create] Limpando safe.directory herdado do host..."
# O VS Code copia o ~/.gitconfig do HOST para dentro do container (para os
# commits saírem com seu nome/e-mail). Mas as entradas `safe.directory` do
# host costumam ser CAMINHOS DO WINDOWS (ex.: F:/...), que no Linux do container
# não são absolutos -> o git imprime "warning: safe.directory '...' not absolute"
# a cada chamada (o prompt chama git para mostrar a branch).
# IMPACTO: mantém nome/e-mail do gitconfig; só apaga os safe.directory inválidos.
git config --global --unset-all safe.directory 2>/dev/null || true
# Confia no diretório do projeto montado (e em qualquer um, dentro do container).
git config --global --add safe.directory /app
git config --global --add safe.directory '*'

# core.fileMode=false: ignora mudanças de BIT DE EXECUÇÃO dos arquivos.
# POR QUÊ: o bind mount Windows->Linux apresenta as permissões/exec-bit
# de forma diferente do que o git gravou no índice. Sem isso, o git do container
# marca TODOS os arquivos como "modificados" (só por causa do modo).
git config --global core.fileMode false

echo "==> [post-create] Configurando o terminal (oh-my-zsh: plugins + tema)..."
# Plugins externos (não vêm no oh-my-zsh). Clonados na pasta custom do omz.
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
if [ -d "$HOME/.oh-my-zsh" ]; then
  git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions \
    "$ZSH_CUSTOM/plugins/zsh-autosuggestions" 2>/dev/null \
    || echo "AVISO: falha ao clonar zsh-autosuggestions"
  git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting \
    "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" 2>/dev/null \
    || echo "AVISO: falha ao clonar zsh-syntax-highlighting"
  # Aplica o nosso .zshrc (tema fino-time + plugins + atalhos do projeto).
  cp /app/.devcontainer/.zshrc "$HOME/.zshrc" \
    || echo "AVISO: não foi possível copiar o .zshrc do projeto"
else
  echo "AVISO: oh-my-zsh não encontrado (feature common-utils não instalou?)."
fi

echo "==> [post-create] Versões instaladas:"
python --version || true
pip --version    || true
uvicorn --version 2>/dev/null || echo "(uvicorn será iniciado pelo CMD do compose)"

echo "==> [post-create] Pronto. App em http://localhost:8000/docs"
