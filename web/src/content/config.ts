import { defineCollection, z } from "astro:content";

const landingsCollection = defineCollection({
  type: "data",
  schema: z.object({
    hero: z.object({
      title: z.string(),
      description: z.string(),
      buttonText: z.string(),
      image: z.string(),
    }),
    pains: z.object({
      title: z.string(),
      items: z.array(
        z.object({
          title: z.string(),
          description: z.string(),
          icon: z.string(),
        })
      ),
    }),
    features: z.object({
      title: z.string(),
      subtitle: z.string(),
      items: z.array(
        z.object({
          title: z.string(),
          description: z.string(),
          icon: z.string(),
          impact: z
            .object({
              metric: z.string(),
              value: z.string(),
              unit: z.string(),
            })
            .optional(),
        })
      ),
      stats: z.object({
        total: z.string(),
        label: z.string(),
        description: z.string(),
      }),
    }),
    howItWorks: z.object({
      title: z.string(),
      subtitle: z.string(),
      steps: z.array(
        z.object({
          number: z.number(),
          title: z.string(),
          description: z.string(),
        })
      ),
    }),
    useCases: z.object({
      title: z.string(),
      subtitle: z.string(),
      primary: z.object({
        title: z.string(),
        description: z.string(),
        image: z.string(),
      }),
      modules: z.array(
        z.object({
          name: z.string(),
          description: z.string(),
          badge: z.string().optional(),
        })
      ),
      secondary: z.object({
        title: z.string(),
        description: z.string(),
        image: z.string(),
      }),
    }),
    testimonials: z.object({
      title: z.string(),
      subtitle: z.string(),
      items: z.array(
        z.object({
          text: z.string(),
          author: z.string(),
          role: z.string(),
          rating: z.number(),
        })
      ),
    }),
    pricing: z.object({
      title: z.string(),
      subtitle: z.string(),
      plans: z.array(
        z.object({
          name: z.string(),
          price: z.string(),
          period: z.string().optional(),
          description: z.string(),
          features: z.array(z.string()),
          highlighted: z.boolean().optional(),
          badge: z.string().optional(),
          buttonText: z.string().optional(),
        })
      ),
    }),
    faq: z.object({
      title: z.string(),
      subtitle: z.string(),
      questions: z.array(
        z.object({
          question: z.string(),
          answer: z.string(),
        })
      ),
    }),
    cta: z.object({
      headline: z.string(),
      subheadline: z.string(),
      buttonText: z.string(),
    }),
  }),
});

export const collections = {
  landings: landingsCollection,
};
