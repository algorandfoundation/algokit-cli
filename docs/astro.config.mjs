// @ts-check
import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';
import remarkGithubAlerts from 'remark-github-alerts';

export default defineConfig({
  site: 'https://algorandfoundation.github.io',
  base: '/algokit-cli/',
  trailingSlash: 'always',
  markdown: {
    remarkPlugins: [remarkGithubAlerts],
  },
  integrations: [
    starlight({
      title: 'AlgoKit CLI',
      tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
      customCss: [
        './src/styles/cli-reference.css',
        'remark-github-alerts/styles/github-colors-light.css',
        'remark-github-alerts/styles/github-colors-dark-media.css',
        'remark-github-alerts/styles/github-base.css',
      ],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/algorandfoundation/algokit-cli',
        },
        {
          icon: 'discord',
          label: 'Discord',
          href: 'https://discord.gg/algorand',
        },
      ],
      sidebar: [
        { label: 'Home', link: '/' },
        {
          label: 'Getting Started',
          items: [
            { slug: 'tutorials/intro' },
            { slug: 'tutorials/smart-contracts' },
            { slug: 'tutorials/algokit-template' },
          ],
        },
        {
          label: 'Features',
          items: [
            { slug: 'features/overview' },
            { slug: 'features/init' },
            { slug: 'features/localnet' },
            { slug: 'features/compile' },
            { slug: 'features/generate' },
            { slug: 'features/config' },
            { slug: 'features/doctor' },
            { slug: 'features/explore' },
            { slug: 'features/dispenser' },
            { slug: 'features/goal' },
            { slug: 'features/completions' },
            {
              label: 'Project Commands',
              collapsed: true,
              items: [
                { slug: 'features/project' },
                { slug: 'features/project/bootstrap' },
                { slug: 'features/project/deploy' },
                { slug: 'features/project/link' },
                { slug: 'features/project/list' },
                { slug: 'features/project/run' },
              ],
            },
            {
              label: 'Tasks',
              collapsed: true,
              items: [
                { slug: 'features/tasks' },
                { slug: 'features/tasks/analyze' },
                { slug: 'features/tasks/ipfs' },
                { slug: 'features/tasks/mint' },
                { slug: 'features/tasks/nfd' },
                { slug: 'features/tasks/opt' },
                { slug: 'features/tasks/send' },
                { slug: 'features/tasks/sign' },
                { slug: 'features/tasks/transfer' },
                { slug: 'features/tasks/vanity_address' },
                { slug: 'features/tasks/wallet' },
              ],
            },
          ],
        },
        {
          label: 'Concepts',
          items: [{ slug: 'concepts/output-stability' }],
        },
        {
          label: 'Architecture Decisions',
          collapsed: true,
          autogenerate: { directory: 'architecture-decisions' },
        },
        {
          label: 'CLI Reference',
          collapsed: true,
          items: [{ slug: 'cli/index', label: 'AlgoKit CLI' }],
        },
      ],
    }),
  ],
});