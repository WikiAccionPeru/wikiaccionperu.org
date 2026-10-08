import { defineCollection, defineContentConfig, z } from '@nuxt/content'

export default defineContentConfig({
  collections: {
    content: defineCollection({
      type: 'page',
      source: '**/*.md',
      schema: z.object({
        type: z.string(),
        date: z.string(),
        modified: z.string().optional(),
        status: z.enum(['publish', 'draft']),
        source_url: z.string().optional(),
        excerpt: z.string().optional(),
        featured_media: z.number().optional(),
        wide: z.boolean().optional(),
        home: z.record(z.string(), z.any()).optional(),
        taxonomies: z.record(z.string(), z.array(z.string())).optional(),
      }),
    }),
  },
})
