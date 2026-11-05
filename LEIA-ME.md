# By the Beach · site

Site estático (sem servidor), pronto para GitHub Pages, como o novo site da Eagle View.

## O que está aqui

| Ficheiro | Para quê |
|---|---|
| `index.html` | O site completo (PT / EN / ES) |
| `img/` | Logótipo, foto aérea e fotos do apartamento |
| `disponibilidade.json` | Datas ocupadas que o calendário mostra |
| `scripts/sync_calendario.py` + `.github/workflows/calendario.yml` | Sincronização automática com Airbnb/Booking (opcional) |

## 1. Formulário → marco_fernandes@me.com (sem o e-mail aparecer)

1. Vai a **web3forms.com**, escreve `marco_fernandes@me.com` e cria a chave (gratuito, 250 pedidos/mês).
2. Recebes um *Access Key* por e-mail.
3. Em `index.html`, procura `COLOCA_AQUI_A_CHAVE_WEB3FORMS` e substitui pela chave.

A chave não revela o e-mail: o Web3Forms entrega os pedidos na caixa associada a ela.
Cada pedido chega com o assunto `Pedido de reserva: 2027-07-10 → 2027-07-17 · Nome`, e o "Responder" vai direto para o hóspede.

## 2. Calendário

**À mão:** edita `disponibilidade.json`. Cada reserva é `{"de": "2027-07-10", "ate": "2027-07-17", "origem": "manual"}`
(`de` = primeira noite, `ate` = dia de saída, que fica livre para a entrada seguinte).
Já está bloqueado até 28 jun 2027, tal como no portal. Com a sincronização ligada, esta data passa a vir do portal.

**Automático, a partir do portal da Feels Like Home:**
1. No GitHub: repositório → Settings → Secrets and variables → Actions → **New repository secret**. Cria dois:
   - `FLH_USER` → o e-mail com que entras no portal
   - `FLH_PASS` → a password do portal
2. Em Actions → "Atualizar calendário" → **Run workflow** para testar. Se ficar verde, está a funcionar. Depois corre sozinho de 3 em 3 horas.

Os segredos ficam encriptados no GitHub: não aparecem no código, no site nem nos registos.
Do portal só se copiam as datas de entrada e saída. Nomes, valores e plataformas ficam lá.
Se o portal falhar (password mudada, portal alterado), o site mantém as últimas datas e o GitHub manda-te um e-mail a avisar.
Se mudares a password do portal, atualiza o segredo `FLH_PASS`.

**Opcional, links iCal:** se um dia tiveres links iCal, cria também o segredo `ICAL_URLS` (um link por linha).

As datas com `"origem": "manual"` nunca são apagadas pela sincronização.

## 3. Publicar no GitHub Pages

1. Cria um repositório novo (ex.: `bythebeach`) e carrega todos os ficheiros desta pasta, incluindo `.github` e `.nojekyll`.
2. Settings → Pages → Source: *Deploy from a branch* → `main` / `root`.
3. Domínio próprio (opcional): Settings → Pages → Custom domain, e no GoDaddy um registo CNAME `www` → `<utilizador>.github.io`.

## Por confirmar antes de publicar

- Distâncias (marina, fortaleza, centro, aeroporto) são aproximadas. A dos 700 m vem do anúncio.
- Não pus preços nem horários de check-in/out porque não estão definidos para reservas diretas.
- As fotos vêm do anúncio do Airbnb e da página do Facebook.
