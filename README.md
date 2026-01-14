# Quizbee

Quizbee is a web application that turns yout study materials (lecture slides, textbooks, etc.) into interactive quizzes.
It provides users with engaging questions, useful feedback and AI-chat where user can discuss questions and answers.

### Try it out yourself! Free tier available: <br>

https://quizbee.academy

### Link to ProductHunt: <br>

https://www.producthunt.com/products/quizbee

# How to run it yourself

### 1. Environment Setup

Copy your `env.example` to a new file named `.env` and fill in all the required API keys.

### 2. External Dependencies

**Important:** This project requires **Redis**, **PocketBase**, and **MeiliSearch** to be running. Since they are not included in your `docker-compose.yml`, ensure the URLs in your `.env` point to active instances.

### 3. Build and Launch

Run the following command in the root directory:

```bash
docker compose up --build
```

It will download all the required packages for all the modules and start the whole app.

# Technical Highlights and Architecture

## Backend (Python FastAPI + ARQ worker) and LLM module

**Core Workflow:** The user uploads study material, which is parsed and split into granular chunks. To generate questions, the system uses RAG to retrieve specific, relevant chunks and feeds them into an LLM. This process is enhanced by BERTopic for extracting semantic themes and LLM chains for complex orchestration, ensuring high-quality, grounded content.

### Modular Monolith with Clean Architecture (DDD)

The backend is engineered as a **Modular Monolith** following **Hexagonal Architecture (Ports & Adapters)**, and **Domain-Driven Design (DDD)** principles. Each module (`quiz_owner`, `document_parser`, etc.) is isolated with clear boundaries between `Domain` (Pure logic), `App` (Use Cases), and `Adapters` (Infrastructure). The system uses a custom **Dependency Injection** container to fully decouple components, ensuring that business logic depends only on abstract interfaces (Ports) rather than concrete implementations. This allows for easy swapping of infrastructure components like LLM providers or databases.

### AI-Native & Multimodal RAG

The system features a custom **Multimodal Document Parsing** pipeline that handles PDF, DOCX, and PPTX files. A standout feature is the automatic extraction of full-page images, which are then processed by **Gemini 2.5 Flash lite** to generate semantic descriptions, making visual content fully searchable and accessible to the LLM.

**Smart Quiz Generation** is powered by **Grok 4.1 fast** (orchestrated via **Pydantic AI** for structured, type-safe interactions). The system orchestrates a **chain of LLMs** to enable query-aware generation: it pre-selects the most relevant chunks via RAG based on the user's specific request before feeding them into the generator. To ensure comprehensive learning, the system employs an **Intelligent Coverage Strategy** that tracks used chunks and deprioritizes them in future generations, aiming for 100% material coverage. It utilizes **BERTopic** to structure unstructured materials into coherent themes. The pipeline generates high-quality embeddings via **Voyage AI**, reduces dimensionality, and applies **K-Means clustering** to mathematically isolate distinct sub-topics. This allows the generator to "walk" through different semantic clusters, ensuring the quiz covers the entire breadth of the material.

For **Smart Context Selection**, a dedicated layer uses **Voyage AI Reranking** to strictly filter noise from retrieved documents. The system treats information as granular **chunks**, limiting the LLM input context to under **3000 tokens** per question generation. This optimization makes the application extremely cost-effective. The generation model is designed to precisely cite and extract only the relevant sub-chunks (pages/sections) needed for each question, effectively "cutting out" the exact material required. This is supported by robust infrastructure including recursive chunking via `Chonkie` and high-quality embeddings via **Voyage AI Embeddings**.

### High-Performance Async Infrastructure

The application is built on **FastAPI** for non-blocking HTTP handling, coupled with **Redis** background workers to handle heavy AI tasks asynchronously. An internal event bus decouples services (e.g., triggering parsing on file upload). Data persistence is handled by **PocketBase** wrapped in strict repository patterns, while **Meilisearch** provides typo-tolerant, lightning-fast full-text search capabilities. Additionally, **Langfuse** is integrated for deep observability, allowing for detailed tracing of LLM chains and monitoring of costs and latency. The entire system is fully containerized using **Docker** and orchestrated via **Docker Compose**, with separate containers for each module (`api`, `worker`, `web`, `app`), ensuring consistent, reproducible environments from development to production.

## Frontend Architecture & Mobile Experience

### Cutting-Edge Stack & Svelte 5

The frontend is a modern hybrid application built with **SvelteKit** and **Capacitor**, fully embracing the new **Svelte 5** for granular, efficient state management. It leverages **Tailwind CSS v4** and **DaisyUI 5** for a highly responsive and customizable UI. The project is structured as a monorepo, utilizing internal packages for shared UI components and design tokens to ensure consistency across the platform.

### Domain-Driven Design (DDD)

Mirroring the backend, the frontend codebase is organized by business domains (e.g., `quiz`, `billing`, `analytics`) rather than technical layers. Each domain encapsulates its own logic, stores, and UI components, making the codebase highly scalable and maintainable. This structure allows for clear separation of concerns and easier navigation for developers working on specific features.

### Native-Like Mobile Experience

The application delivers a native-like experience on iOS and Android through **Capacitor**. It implements **Persistent Authentication** using native storage to keep users logged in securely across app restarts. Custom touch gesture handling (e.g., swipe-to-open sidebars) and responsive design logic ensure the app feels fluid and intuitive on touch devices.

### Real-Time Reactive State

State management is powered by **Svelte 5** combined with **PocketBase Realtime** subscriptions.
