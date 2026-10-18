# Aurora Zero

Jogo original de tiro 2D em Python com pygame-ce, criado para a atividade de demonstração. A nave do jogador é desenhada pelo próprio código; os cenários, a nave inimiga, o projétil inimigo e a música usam os assets entregues com o material da atividade.

## Como jogar

- **WASD** ou **setas**: mover
- **Espaço**: disparar (segure para disparo contínuo)
- **P**: pausar ou continuar
- **Esc**: voltar ao menu
- **V**: alternar a música

Derrube 12 drones para vencer. O jogador começa com 3 vidas; colisões com drones ou projéteis inimigos tiram uma vida.

## Executar no computador

Instale Python 3.10 ou superior. No terminal, dentro desta pasta:

```text
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py main.py
```

No macOS ou Linux, use `python3` no lugar de `py` e ative o ambiente com `source .venv/bin/activate`.

## Criar a entrega para Windows

Em um computador Windows com Python instalado, dê dois cliques em `build_windows.bat`. O script instala o PyInstaller, cria o executável e prepara `dist/AuroraZero-Windows.zip` com o `.exe`, a pasta `assets` e este README. O ZIP de entrega pode ser enviado ao professor.

Para executar uma build com janela de console e visualizar mensagens de erro, use no terminal:

```text
py -m PyInstaller --noconfirm --onefile --name AuroraZero main.py
```

Copie também a pasta `assets` para junto do `dist/AuroraZero.exe`. A versão normal criada pelo arquivo `.bat` abre apenas a janela do jogo.

## Verificação rápida

```text
py main.py --self-test
```

O teste carrega os assets e desenha um quadro sem iniciar a partida.
