<!-- 20261121-001 -->

## dsh-relay Docker 验证（2026-11-21，本…

dsh-relay Docker 验证（2026-11-21，本机 Docker Desktop 28.4.0 可用；引擎只走命名管道，沙箱下必须用 danger-full-access 调 docker）。

Docker Hub 不可达（registry-1.docker.io 直连被拒），且本地无缓存镜像，所以改用离线路径：新增 server/Dockerfile.offline（FROM scratch + 预编译静态 linux/amd64 二进制）、server/scripts/build-offline-image.sh、compose 默认 build Dockerfile.offline；

镜像 dsh-relay-server:0.2.0 仅 11.5MB，零基础镜像拉取。

### 验证

容器以 --read-only + 65532:65532 启动，自签证书（SAN localhost/127.0.0.1）下 curl --cacert 健康检查通过；用真实客户端跑通容器化端到端（wss 登录、建房/进房、presence、私聊、广播、文件上传去重+拉取校验、离线补投）全 PASS。

过程中抓到并修掉一个真 bug：客户端 dataRequest 沿用旧 ws→http 逻辑，把 https baseUrl 改成了 http，导致 HTTPS 部署下文件分片 PUT 报 400；

改为 `${baseUrl}${route}`（保留 path 前缀）并加单测，客户端 58 条测试全过，提交 fa5b6b5。

镜像已导出 dist/dsh-relay-server-0.2.0.tar（3.4MB），可在 Debian 上 docker load 后用 docker compose up -d --no-build。

### 仍未验证

真实 Debian 主机部署、真实 CA 证书；本机 Ubuntu VM 无 Docker 且 sudo 需密码，不能当构建机。scratch 镜像无 tzdata，日志为 UTC。
