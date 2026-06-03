# =============================================================================
# .zshrc do devcontainer — CloudTask AI SaaS (Semana 1)
# -----------------------------------------------------------------------------
# Copiado para ~/.zshrc pelo post-create.sh. Configura o oh-my-zsh com um tema
# de DUAS LINHAS, plugins úteis e atalhos do projeto.
#
# POR QUÊ o tema "fino-time": mostra, em duas linhas, usuário@host, diretório
# atual, branch do git e a hora — exatamente o "onde estou?" que ajuda o aluno.
# Usa só caracteres comuns; funciona sem Nerd Font.
# =============================================================================

export ZSH="$HOME/.oh-my-zsh"

# Tema de duas linhas com bastante informação.
ZSH_THEME="fino-time"

# Plugins do oh-my-zsh (semana 1: só o essencial; AWS/k8s entram depois).
plugins=(
  git
  docker
  docker-compose
  python
  pip
  vscode
  colored-man-pages
  zsh-autosuggestions
  zsh-syntax-highlighting
)

source "$ZSH/oh-my-zsh.sh"

# ----- VS Code: shell integration -------------------------------------------
# Habilita "sticky scroll" (linha do comando fixa no topo enquanto rolamos),
# decorações de prompt/exit code e command markers. Procura o script
# `shellIntegration.zsh` de 2 formas (oficial via `code`, depois fallback).
if [[ "$TERM_PROGRAM" == "vscode" ]]; then
    _vsc_int=""
    if command -v code &>/dev/null; then
        _vsc_int="$(code --locate-shell-integration-path zsh 2>/dev/null)"
    fi
    if [[ -z "$_vsc_int" || ! -f "$_vsc_int" ]]; then
        _vsc_int="$(find ~/.vscode-server -name 'shellIntegration.zsh' 2>/dev/null | head -1)"
    fi
    if [[ -n "$_vsc_int" && -f "$_vsc_int" ]]; then
        . "$_vsc_int"
    fi
    unset _vsc_int
fi

# ----- Histórico de comandos -------------------------------------------------
# Guardamos o histórico em /commandhistory (volume), então sobrevive a rebuilds.
HISTFILE=/commandhistory/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_IGNORE_SPACE

# Binários Python instalados com `pip install --user`.
export PATH="$HOME/.local/bin:$PATH"

# ----- Atalhos do projeto ----------------------------------------------------
alias dc='docker compose'
alias dcup='docker compose up'
alias dcdown='docker compose down'
alias dclogs='docker compose logs -f api'
alias serve='uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload'
alias health='curl -s http://localhost:8000/health; echo'

# ----- Prompt "transient" ----------------------------------------------------
# Quando Enter é pressionado, a linha rodada é redesenhada com prompt mínimo
# ("[data] > comando"), deixando o histórico limpo. A próxima linha volta ao
# prompt cheio.
#
# Implementado via `zle-line-finish` + `precmd` (NÃO via bindkey ^M) para não
# sobrescrever o widget `accept-line` do VS Code (que precisa enviar os markers
# OSC 633 do shell integration).
typeset -g _CT_FULL_PROMPT="$PROMPT"
typeset -g _CT_FULL_RPROMPT="$RPROMPT"

_ct_transient_line_finish() {
    # Mantém os markers OSC 633 do VS Code shell integration:
    #   \e]633;A\a = início do prompt (sticky scroll ancora aqui)
    #   \e]633;B\a = fim do prompt / início do comando
    PROMPT=$'%{\e]633;A\a%}%F{8}[%D{%Y-%m-%d %H:%M:%S}]%f > %{\e]633;B\a%}'
    RPROMPT=''
    zle reset-prompt
}
zle -N zle-line-finish _ct_transient_line_finish

autoload -Uz add-zsh-hook
_ct_transient_restore_precmd() {
    PROMPT="$_CT_FULL_PROMPT"
    RPROMPT="$_CT_FULL_RPROMPT"
}
add-zsh-hook precmd _ct_transient_restore_precmd

# Mensagem de boas-vindas.
echo "CloudTask AI SaaS (Semana 1) — devcontainer. App em http://localhost:8000/docs | logs: dclogs"
