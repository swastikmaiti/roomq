# Agent Meeting Room — frontend image (local/dev parity).
# Production deploys to Cloudflare Pages via @cloudflare/next-on-pages (see
# docs/deployment.md §5); this Dockerfile just runs the standard Next.js server.
FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# NEXT_PUBLIC_API_URL is inlined at build time; pass it as a build arg in prod.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
