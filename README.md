# LinSnipper

Ferramenta de captura de tela para Linux inspirada no Snipping Tool do Windows 11.

## Funcionalidades

- Modos de captura:
  - Retângulo
  - Forma livre
  - Janela (via seleção)
  - Tela cheia
- Delay configurável (0, 3, 5, 10 segundos)
- Editor com:
  - Caneta
  - Marcador
  - Borracha
  - Undo/Redo
  - Copiar para a área de transferência
  - Salvar / Salvar como (PNG/JPEG)
- Estrutura em camadas (core/infra/ui) com logging e configuração persistente.

## Requisitos

- Python 3.10+
- Qt (biblioteca usada via PySide6)
- Biblioteca Python:
  - `PySide6`

Instale as dependências com:

```bash
pip install PySide6
```

Ou, se preferir, instale o pacote em modo desenvolvimento:

```bash
pip install -e .
```

## Uso

Iniciar o editor vazio:

```bash
linsnipper
```

Iniciar diretamente em modo de captura (tipo Win+Shift+S):

```bash
linsnipper --snip
```

Modos de captura disponíveis:

```bash
linsnipper --snip --mode rect        # retângulo
linsnipper --snip --mode freeform    # forma livre
linsnipper --snip --mode window      # janela (via seleção)
linsnipper --snip --mode fullscreen  # tela cheia
```

Delay antes da captura:

```bash
linsnipper --snip --mode rect --delay 3
```

Log detalhado no console (além do arquivo de log):

```bash
linsnipper --snip --log-console
```

## Atalho de teclado

Você pode criar um atalho global no seu ambiente gráfico (GNOME, KDE, etc.):

- **Atalho**: `Super+Shift+S`
- **Comando**: `linsnipper --snip`

Para usuários GNOME, há um script facilitador:
```bash
./scripts/setup_gnome_shortcut.sh
```

## Estrutura do projeto

```text
lin-snipper/
├─ pyproject.toml
├─ README.md
└─ src/
   └─ linsnipper/
      ├─ __init__.py
      ├─ __main__.py
      ├─ cli.py
      ├─ app.py
      ├─ config.py
      ├─ logging_config.py
      ├─ errors.py
      ├─ core/
      │  ├─ __init__.py
      │  ├─ models.py
      │  ├─ interfaces.py
      │  ├─ capture_service.py
      │  └─ undo.py
      ├─ infra/
      │  ├─ __init__.py
      │  ├─ platform.py
      │  └─ qt_capture_backend.py
      └─ ui/
         ├─ __init__.py
         ├─ drawing_canvas.py
         ├─ editor_window.py
         └─ snip_overlay.py
```

## Licença

Defina a licença que preferir (por exemplo, MIT) e adicione o arquivo `LICENSE`.
