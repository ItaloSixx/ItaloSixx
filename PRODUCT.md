# PRODUCT.md

**Perfil GitHub de Ítalo Jeferson (ItaloSixx).**

## O que é
Um README de perfil no GitHub — a primeira tela que alguém vê depois do avatar.
Não é produto SaaS, não tem funil. É uma vitrine de identidade técnica.

## Modo
**Experience.** O artefato lidera; a interface recua. O visitante está dentro do trabalho.

## Público e cena
Recrutador técnico, colega dev, alguém que chegou por um repositório e clicou no
perfil. Olha por 10 a 30 segundos, no desktop ou no celular, vindo do GitHub.

## O que a primeira tela precisa provar
Que ele constrói software de verdade — backend, mobile e firmware — e que tem
critério visual. Não que "sabe fazer dashboard".

## Ação
Abrir LinkedIn, portfólio ou e-mail. Secundário: entrar no jogo.

## Verdade do produto (dados reais, nada inventado)
- 369 commits, 22 repositórios públicos, desde 2023
- 9 releases
- Stack: Java (backend/android), PHP (Laravel/APIs), Flutter, C (firmware ESP32), Python
- Jogo Snake jogável em italosixx.github.io/ItaloSixx

## Restrições
- GitHub renderiza HTML sanitizado: sem JS, sem CSS externo. SVG estático é o teto.
- SMIL funciona em SVG; JS não.
- Imagens escalam para ~308px no celular e ~846px no desktop.
- Deve rodar sem serviço de terceiros: SVGs gerados e versionados.
