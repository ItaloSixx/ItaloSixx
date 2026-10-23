# DESIGN.md

## Mundo visual
Tela de fliperama em attract mode. Não é "gamer aesthetic" de sticker — é o
vocabulário real do hardware: fósforo verde sobre preto, uma única tipografia
de ROM, letreiro desenhado célula a célula, inimigos marchando em passo discreto.

## Paleta
- ground `#08090B` — preto levemente azulado, como vidro de CRT apagado
- ink `#E8E8E6` — branco fosforescente, não branco puro
- dim `#7C7F86` — rótulos de dado
- phosphor `#4BE38C` — único acento primário
- amber `#F0B24A` — ênfase única: o pico do gráfico e o link do jogo

## Tipografia
Uma só: bitmap 5x7 autoral, desenhado em retângulos no gerador.
Não é fonte do sistema fingindo ser pixel — são as letras que eu desenhei.
Maiúsculas, sem acento (limite do ROM). Caixa alta em tudo.

## Regras
- Sem kicker/eyebrow acima de título.
- Sem trio de números grandes com rótulo embaixo.
- Sem sombra dura deslocada, sem gradiente, sem blur decorativo.
- Sem glifo Unicode no lugar de ícone.
- Sem números decorativos (STAGE 04, CREDIT 01) — cada número é um dado real.
- Um momento de movimento autoral por tela, o resto parado.

## Entrega
SVGs 880 (desktop) + 440 (mobile), servidos por `<picture>`.
