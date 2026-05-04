# GlicoTrack — Documento de Definição do Projeto

## Visão Geral

App web responsivo para acompanhamento de glicemia de paciente com **diabetes Tipo 2**. O objetivo principal é permitir que o paciente registre suas medições diárias e que ele e seus responsáveis acompanhem a evolução, com geração de relatórios para consultas médicas.

---

## Público-Alvo

| Perfil | Papel |
|---|---|
| Paciente | Registra as medições e dados do dia a dia |
| Pais / Responsáveis | Acompanham remotamente e também podem registrar dados |

Todos os perfis compartilham os mesmos dados em nuvem. O acesso é feito via login individual com e-mail e senha.

---

## Funcionalidades Principais

### 1. Registro de Glicemia
- Medições em horários específicos e configuráveis do dia
- Suporte a dois métodos de medição:
  - **Glicosímetro** (medição pontual via picada no dedo)
  - **Sensor contínuo (CGM)** — ex: FreeStyle Libre
- Identificação do momento da medição:
  - Jejum (ao acordar)
  - Antes das refeições
  - 2h após as refeições
  - Outro (livre)

### 2. Registro de Dados Complementares
- **Refeições:** descrição do que foi consumido
- **Atividade física:** tipo e duração
- **Medicamentos:** configurável pelo usuário (insulina, medicação oral ou nenhum)
- **Sintomas:** seleção de lista (tontura, fraqueza, suor frio, etc.) + campo livre
- **Peso e pressão arterial**

### 3. Visualização e Histórico
- Gráfico de glicemia ao longo do dia e da semana
- Indicador visual por cor:
  - Verde: dentro da faixa ideal
  - Amarelo: limite (atenção)
  - Vermelho: fora da faixa (alerta)
- Histórico completo de registros com filtro por data
- Painel resumo com médias e tendências

### 4. Alertas e Notificações
- Notificação quando a glicemia registrada estiver fora da faixa de referência
- Lembrete nos horários configurados para registrar a medição

### 5. Relatório para o Médico
- Geração de relatório em **PDF**
- Período configurável (ex: últimos 15 ou 30 dias)
- Inclui: gráficos, médias, registros de medicação, sintomas e observações
- Fácil de enviar por e-mail ou WhatsApp

---

## Faixas de Referência (Diabetes Tipo 2)

| Momento | Normal | Atenção | Alerta |
|---|---|---|---|
| Jejum | < 100 mg/dL | 100–125 mg/dL | ≥ 126 mg/dL |
| Pós-prandial (2h) | < 140 mg/dL | 140–179 mg/dL | ≥ 180 mg/dL |

> Essas faixas seguem as referências padrão. O app deve permitir ajuste personalizado no futuro, conforme orientação médica.

---

## Autenticação e Acesso

- Login com **e-mail e senha** (gerenciado pelo Supabase Auth)
- Dados compartilhados entre paciente e responsáveis via vínculo familiar
- Armazenamento em **nuvem** (Supabase)

---

## Stack Técnica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Backend | **Python + FastAPI** | Leve, moderno, compatível com Vercel serverless |
| Frontend | **Jinja2 + Tailwind CSS** | Templates server-side responsivos sem complexidade JS |
| Banco de dados + Auth | **Supabase** (PostgreSQL) | Auth pronta, banco gerenciado, conta já existente |
| Geração de PDF | **WeasyPrint** ou **ReportLab** | Bibliotecas Python maduras para relatórios |
| Hospedagem | **Vercel** | Conta já existente, suporte a Python serverless |

---

## Requisitos de Interface

- Responsivo: funciona em qualquer tamanho de tela (celular, tablet, desktop)
- App web acessado pelo navegador — sem necessidade de App Store
- Interface simples e objetiva, pensada para uso diário por não-técnicos

---

## Fora do Escopo (v1)

- Integração automática com aparelhos de glicosímetro ou CGM (dados inseridos manualmente)
- Inteligência artificial ou recomendações automáticas de dieta/insulina
- Teleconsulta ou chat com médico
- App nativo iOS/Android

---

## Próximos Passos Sugeridos

1. Definir o modelo de dados (tabelas no Supabase)
2. Criar wireframes das telas principais (dashboard, registro, relatório)
3. Configurar projeto FastAPI com autenticação via Supabase
4. Implementar o fluxo de registro de glicemia
5. Implementar visualizações e gráficos
6. Implementar geração de PDF
7. Deploy no Vercel

---

*Documento criado em: 2026-04-29*
