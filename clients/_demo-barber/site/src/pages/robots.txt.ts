// robots.txt: allow everything except a synthetic demo site, and point to the sitemap.
import type { APIRoute } from 'astro';
import config from '../../site.config.json';

export const GET: APIRoute = () => {
  const sitemap = new URL('/sitemap-index.xml', config.site_url).href;
  const rules = config.synthetic ? 'User-agent: *\nDisallow: /\n' : 'User-agent: *\nAllow: /\n';
  return new Response(`${rules}\nSitemap: ${sitemap}\n`, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
