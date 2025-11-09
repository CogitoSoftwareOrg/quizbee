import { blogCollectionPb } from "./blog";
import { landingsCollection, landingsCollectionPb } from "./landings";
import { pagesCollection } from "./pages";

export const collections = {
  pages: pagesCollection,
  landings: landingsCollection,
  // blog: blogCollection,
  blogPb: blogCollectionPb,
  landingsPb: landingsCollectionPb,
};
