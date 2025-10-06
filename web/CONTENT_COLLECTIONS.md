# Content Collections для Многоязычных Лендингов

## 📦 Структура

```
src/
├── content/
│   ├── index.ts                    # Определение коллекций и схем
│   └── landings/
│       ├── en/
│       │   └── quizbee-base.json  # Английский контент
│       └── ru/
│           └── quizbee-base.json  # Русский контент
├── i18n/
│   ├── ui.ts                       # Языковые настройки
│   └── utils.ts                    # Утилиты (добавлена getLandingContent)
└── pages/
    └── [...lang]/
        └── index.astro             # Главная страница (использует коллекции)
```

## 🚀 Как Это Работает

### 1. **Схема Коллекции** (`src/content/index.ts`)

Определяет структуру контента для всех секций лендинга:

- `hero` - главная секция
- `pains` - боли пользователей
- `features` - фичи продукта
- `howItWorks` - как работает
- `useCases` - сценарии использования
- `testimonials` - отзывы
- `pricing` - тарифы
- `faq` - вопросы-ответы
- `cta` - призыв к действию

### 2. **JSON Файлы с Контентом**

Каждый язык имеет свой JSON файл в соответствующей директории:

- `en/quizbee-base.json` - английская версия
- `ru/quizbee-base.json` - русская версия

### 3. **Автоматический Выбор Языка**

```astro
// В index.astro
const lang = getLangFromUrl(Astro.url);  // Получаем язык из URL

const entries = await getCollection("landings");
const landingEntry = entries.find(
  (entry) => entry.id === `${lang}/quizbee-base.json`
);

const content = landingEntry.data;  // Контент на нужном языке
```

### 4. **Использование Контента**

```astro
<Hero
  title={content.hero.title}
  description={content.hero.description}
  buttonText={content.hero.buttonText}
  image={content.hero.image}
/>
```

## ✏️ Добавление Нового Языка

1. Добавьте язык в `src/i18n/ui.ts`:

```typescript
export const languages = {
  en: "English",
  ru: "Русский",
  es: "Español", // Новый язык
};
```

2. Создайте директорию и JSON файл:

```bash
mkdir src/content/landings/es
cp src/content/landings/en/quizbee-base.json src/content/landings/es/
```

3. Переведите контент в `es/quizbee-base.json`

4. Готово! Система автоматически подхватит новый язык.

## 📝 Создание Нового Лендинга

1. Создайте новый JSON файл (например, `quizbee-pro.json`):

```bash
cp src/content/landings/en/quizbee-base.json src/content/landings/en/quizbee-pro.json
```

2. Создайте новую страницу:

```astro
// src/pages/[...lang]/pro.astro
const landingEntry = entries.find(
  (entry) => entry.id === `${lang}/quizbee-pro.json`  // Новое имя
);
```

3. Переиспользуйте те же компоненты секций!

## 🎯 Преимущества Подхода

✅ **Разделение Контента и Кода**

- Контент в JSON, логика в компонентах

✅ **Типобезопасность**

- Zod схемы валидируют структуру

✅ **Легко Добавлять Языки**

- Просто создайте новый JSON файл

✅ **Переиспользование Компонентов**

- Одни и те же компоненты для всех языков

✅ **Автоматическая Валидация**

- Astro проверяет соответствие схеме при сборке

## 🔧 API Утилиты

### `getLandingContent(lang, landingName?)`

Утилита в `src/i18n/utils.ts` для получения контента:

```typescript
import { getLandingContent } from "@/i18n/utils";

const content = await getLandingContent("en", "quizbee-base");
```

**Особенности:**

- Автоматический fallback на `defaultLang`, если перевод не найден
- TypeScript типы из схемы коллекции
- Бросает ошибку, если контент не существует

## 📊 Примеры URL

```
/                    → Английская версия (default)
/en                  → Английская версия
/ru                  → Русская версия
/es                  → Испанская версия (если добавлена)
```

## 🐛 Отладка

### Проверка Доступных Записей

```astro
const entries = await getCollection("landings");
console.log("Available entries:", entries.map(e => e.id));
```

### Проверка Структуры Контента

```astro
const content = landingEntry.data;
console.log("Content keys:", Object.keys(content));
```

## 📚 Дополнительно

- [Astro Content Collections](https://docs.astro.build/en/guides/content-collections/)
- [Zod Schema Validation](https://zod.dev/)
- [Astro i18n Routing](https://docs.astro.build/en/guides/internationalization/)
