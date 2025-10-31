import Hero from "./Hero.astro";
import Pains from "./Pains.astro";
import Features from "./Features.astro";
import HowItWorks from "./HowItWorks.astro";
import Products from "./Products.astro";
import Testimonials from "./Testimonials.astro";
import Pricing from "./Pricing.astro";
import FAQ from "./FAQ.astro";
import CTA from "./CTA.astro";

export type HeroProps = Parameters<typeof Hero>[0];
export type PainsProps = Parameters<typeof Pains>[0];
export type FeaturesProps = Parameters<typeof Features>[0];
export type HowItWorksProps = Parameters<typeof HowItWorks>[0];
export type ProductsProps = Parameters<typeof Products>[0];
export type TestimonialsProps = Parameters<typeof Testimonials>[0];
export type PricingProps = Parameters<typeof Pricing>[0];
export type FAQProps = Parameters<typeof FAQ>[0];
export type CTAProps = Parameters<typeof CTA>[0];

// A discriminated union you can reuse in your DB/API layer
export type SectionDef =
  | { type: "Hero"; props: HeroProps }
  | { type: "Pains"; props: PainsProps }
  | { type: "Features"; props: FeaturesProps }
  | { type: "HowItWorks"; props: HowItWorksProps }
  | { type: "Products"; props: ProductsProps }
  | { type: "Testimonials"; props: TestimonialsProps }
  | { type: "Pricing"; props: PricingProps }
  | { type: "FAQ"; props: FAQProps }
  | { type: "CTA"; props: CTAProps };

export type LandingDef = {
  meta: {
    title: string;
    description?: string;
    image?: string;
    active?: string;
    headerCtaHref?: string;
    structuredData?: Record<string, any>;
  };
  sections: SectionDef[];
};
