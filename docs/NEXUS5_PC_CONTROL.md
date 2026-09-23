# NEXUS 5.0 — Controle do PC

O NEXUS 5.0 adiciona uma camada de controle do computador baseada em Skills, Planner, Security Manager e Command Pipeline.

## Arquivos

As pastas autorizadas ficam em `data/paths.json`.

Exemplos de aliases:

- `desktop`
- `documents`
- `downloads`
- `pictures`
- `videos`
- `music`
- `project`

O NEXUS não deve acessar caminhos fora dessas raízes.

Exemplos:

```text
liste meus downloads
mostre os arquivos de downloads
procure arquivo trabalho na pasta downloads
abra o arquivo trabalho.pdf
crie uma pasta chamada Projetos em desktop
mova trabalho.pdf para documents
```

## Aplicações

Aplicativos autorizados são configurados em `data/applications.json`.

Exemplo:

```json
{
  "spotify": {
    "path": "%APPDATA%\\Spotify\\Spotify.exe",
    "process": "Spotify.exe"
  }
}
```

Adicionar um programa novo normalmente exige apenas cadastrar seu caminho e processo nesse JSON.

## Processos

`data/processes.json` controla quais processos podem ser encerrados pela Skill de processos.

Exemplos:

```text
quais processos estão rodando
feche o processo spotify.exe
```

Listar processos é uma ação de baixo risco. Encerrar processos é risco médio, então exige UNLOCK + confirmação.

## Segurança

- `file_list`, `file_find`, `file_open`, `file_create_folder`, `process_list`: baixo risco.
- `file_move`, `close_application`, `process_close`: risco médio; exige UNLOCK + confirmação.
- `file_delete`: alto risco; exige UNLOCK + confirmação explícita.

O modo `LOCK` bloqueia ações de risco médio e alto.

## Pipeline

Uma meta como:

```text
abra o Spotify, liste meus downloads e mostre os processos
```

pode virar uma sequência:

```text
1. open_application
2. file_list
3. process_list
```

O pipeline executa em ordem e interrompe a sequência quando uma etapa falha.

## Resultado entre etapas

O Planner pode usar `$last_file` quando uma etapa seguinte depende do arquivo encontrado anteriormente.

Exemplo conceitual:

```text
procure o arquivo trabalho e depois abra ele
```

O plano pode ser convertido em:

```text
1. file_find
2. file_open(path=$last_file)
```

O Pipeline substitui o placeholder pelo primeiro arquivo encontrado antes de executar a segunda etapa.
