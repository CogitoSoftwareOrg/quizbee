# 🐝 Quizbee

**Turn your study materials into interactive quizzes instantly.**

Quizbee is a powerful web application that transforms lecture slides, textbooks, and notes into engaging quizzes. It features an AI-chat assistant to discuss questions and answers, providing deep feedback to help you learn faster.

### 🔗 Quick Links


**ProductHunt:** [Support us on ProductHunt](https://www.producthunt.com/products/quizbee)

---

# 🚀 How to Run It Yourself

### 1. Environment Setup
Start by copying the `env.example` file to a new file named `.env` and filling in all the required API keys to configure the application secrets.

### 2. External Dependencies
**⚠️ Important:** This project relies on **Redis**, **PocketBase**, and **MeiliSearch** running externally. These services are *not* included in the `docker-compose.yml`, so you must ensure the URLs in your `.env` file point to active, accessible instances of these services.

### 3. Build and Launch
Once your environment is configured, run the following command in the root directory. This will download all required packages for every module and launch the full application stack:

```bash
docker compose up --build
```

It will download all the required packages for all the modules and start the whole app.

# 🛠️ Technical Highlights & Architecture

### 🔙 Backend & AI Module

**Core Workflow & Architecture**
The backend is engineered as a **Modular Monolith** using **Python FastAPI**. We follow **Domain-Driven Design (DDD)** and **Hexagonal Architecture**, ensuring business logic remains pure and isolated from infrastructure. A custom Dependency Injection container allows us to easily swap out components (like databases or LLM providers) without touching the core logic. The workflow begins when a user uploads study material, which is parsed into granular chunks. The system uses RAG to retrieve relevant segments and feeds them into an LLM, enhanced by **BERTopic** for thematic consistency and complex chains for orchestration.

**AI-Native RAG & Smart Coverage**
Our custom pipeline handles PDFs, DOCXs, and PPTXs. Uniquely, we extract full-page images and process them with **Gemini 2.5 Flash lite** to make visual charts and diagrams fully searchable. For quiz generation, we use **Grok 4.1 fast** orchestrated via **Pydantic AI** for structured output. To ensure comprehensive learning, we employ an **Intelligent Coverage Strategy** that tracks used chunks and deprioritizes them in future quizzes. By utilizing **Voyage AI** for embeddings and reranking alongside **K-Means clustering**, the AI "walks" through different semantic topics (BERTopic) to cover the full breadth of the material, all while limiting context to under 3000 tokens for cost efficiency.

**Infrastructure & Observability**
We use **Redis** workers for background tasks and **Meilisearch** for lightning-fast, typo-tolerant search. Data is secured in **PocketBase** using strict repository patterns. For monitoring, **Langfuse** provides deep observability into LLM chains, costs, and latency.

### 🎨 Frontend & Mobile Experience

**Cutting-Edge Stack & Native Feel**
The frontend is a modern hybrid application built with **SvelteKit** and **Capacitor**, fully embracing **Svelte 5** for granular state management. We style the application using **Tailwind CSS v4** and **DaisyUI 5**, organized within a monorepo that shares UI components across the platform. Thanks to Capacitor, Quizbee offers a native experience on iOS and Android, including features like **Persistent Authentication** and custom touch gestures. Real-time reactivity is seamlessly handled by combining Svelte 5 runes with **PocketBase Realtime** subscriptions.
