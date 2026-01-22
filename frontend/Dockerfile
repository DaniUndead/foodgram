# build env
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
RUN npm install ajv@8.12.0
COPY . ./
RUN npm run build
CMD cp -r build result_build
