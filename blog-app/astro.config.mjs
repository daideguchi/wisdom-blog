import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Enable Markdown processing from parent directory
  markdown: {
    // Allow access to parent directory for articles
    drafts: true,
  },
  // Content collections configuration will be added here
});