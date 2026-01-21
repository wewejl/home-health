# 构建阶段 - 使用阿里云镜像加速
FROM docker.1ms.run/library/node:20-alpine AS builder

WORKDIR /app

# API 地址（构建时传入，默认生产环境使用相对路径）
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 配置淘宝 npm 镜像加速
RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段 - 使用阿里云镜像加速
FROM docker.1ms.run/library/nginx:alpine

# 复制构建产物到nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
