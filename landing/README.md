# Vertice-Code Landing Page

Uma landing page moderna para expor o serviço Vertice-Code, uma plataforma revolucionária de IA coletiva.

## 🌟 Visão Geral

Esta landing page apresenta o Vertice-Code como a próxima evolução da inteligência artificial, focando em:

- **IA Coletiva**: Sistemas que aprendem uns com os outros
- **Multi-LLM Orchestration**: Coordenação inteligente entre diferentes modelos
- **MCP Protocol**: Comunicação seamless entre agentes
- **Aprendizado Distribuído**: Evolução contínua através da colaboração

## 🚀 Funcionalidades

### Design Responsivo
- Layout moderno e adaptável para todos os dispositivos
- Animações suaves e interativas
- Interface intuitiva e acessível

### API Integration
- Demonstração ao vivo da API MCP
- Teste interativo de endpoints
- Documentação clara dos métodos disponíveis

### Recursos Interativos
- Contadores animados de estatísticas
- Formulário de contato funcional
- Navegação suave por seções
- Animações de scroll

## 📁 Estrutura do Projeto

```
landing/
├── index.html          # Página principal
├── styles.css          # Estilos CSS modernos
├── script.js           # JavaScript interativo
└── README.md           # Esta documentação
```

## 🎨 Assets Necessários

Para uma experiência visual completa, considere criar os seguintes assets:

### Imagens e Ícones
- Logo do Vertice-Code (SVG/PNG)
- Ícones personalizados para cada seção
- Imagens de background para hero section
- Avatares para a seção de comunidade

### Animações
- Vídeo demonstrativo da rede neural
- GIFs animados mostrando funcionalidades
- Micro-interações para botões e elementos

### Paleta de Cores Personalizada
- Gradientes para destaques
- Tema dark/light mode
- Cores acessíveis para todos os usuários

## 🔧 Configuração de Deploy

### Firebase Hosting (Recomendado)

1. Instalar Firebase CLI:
```bash
npm install -g firebase-tools
```

2. Inicializar projeto:
```bash
firebase init hosting
```

3. Configurar `firebase.json`:
```json
{
  "hosting": {
    "public": "landing",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

4. Deploy:
```bash
firebase deploy --only hosting
```

### Outras Opções
- **Vercel**: Deploy automático via Git
- **Netlify**: CI/CD integrado
- **GitHub Pages**: Hospedagem gratuita

## 🌐 Endpoints da API

A landing page integra com os seguintes endpoints:

- `GET /health` - Status do servidor
- `POST /mcp` - API JSON-RPC principal
- `GET /` - Interface web do servidor

**URL de Produção:** https://vertice-mcp-server-452089804714.us-central1.run.app

## 📊 Métricas e Analytics

### Integração Recomendada
- Google Analytics 4
- Hotjar para heatmaps
- Mixpanel para eventos customizados

### Eventos Principais
- Cliques em "Experimentar API"
- Testes da API realizados
- Submissões do formulário de contato
- Tempo gasto em cada seção

## 🔒 Segurança

- Formulário de contato com validação
- Rate limiting para API calls
- HTTPS obrigatório
- Content Security Policy

## 📱 Responsividade

Testado em:
- Desktop (1920px+)
- Tablet (768px - 1024px)
- Mobile (320px - 767px)

## 🎯 Próximos Passos

1. **Deploy da Landing Page**
2. **Integração com Analytics**
3. **Otimização SEO**
4. **A/B Testing**
5. **Internacionalização (i18n)**

## 🤝 Contribuição

Para contribuir com melhorias na landing page:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é parte do ecossistema Vertice-Code e segue a mesma licença do projeto principal.

---

**Criado com ❤️ para a evolução da IA coletiva**
