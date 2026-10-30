FROM node:22-bookworm-slim

ENV NODE_ENV=production \
    PORT=8000 \
    HOSTNAME=0.0.0.0

WORKDIR /app
COPY dist/standalone ./
RUN npm pkg set 'overrides.image-size=2.0.4' 'overrides.satori=0.33.5' 'overrides.fflate=0.7.5' \
    && npm install --omit=dev --no-save \
      vinext@1.0.0-beta.5 \
      react@19.2.8 \
      react-dom@19.2.8 \
      react-server-dom-webpack@19.2.8 \
    && npm cache clean --force

EXPOSE 8000

USER node

CMD ["node", "server.js"]
