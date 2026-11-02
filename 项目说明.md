# LLBot + PMHQ7 / QQ 3.2.31 兼容项目包

**特别鸣谢 [@hairuiaa](https://github.com/hairuiaa)。**

本包整理了2026-11-02在新机完成有限真实收发验证并切换的兼容方案：LLBot `8.3.2-selfhost.2` + 官方PMHQ `7.3.2` + QQ Linux `3.2.31-51102`。不需要LLBot平台注册Token，本地WebUI密码和API认证继续保留。

这是PMHQ7搭配较新版QQ的兼容方案，不是PMHQ9原生源码重编译版。PMHQ原生二进制没有改动；只附官方7.3.2发布组件和验证过的偏移/启动配置。扫码和真实QQ登录校验仍正常执行。

## 包含哪些内容

| 目录/文件 | 内容 |
|---|---|
| `source/` | LLBot Fork源码、锁文件、构建工具入口、测试及GPL许可 |
| `runtime/` | 已构建LLBot主程序、WebUI、运行依赖，主程序摘要与新机一致 |
| `native/` | PMHQ7.3.2 x86_64可执行程序和libpmhq.so |
| `config/` | 已清空账号字段的偏移配置、无实际凭证的LLBot配置模板 |
| `deploy/` | 实际部署的进程监督启动器、独立安装Dockerfile、初始化脚本、Nginx例子 |
| `docs/` | 部署、验证、限制、回滚与备份说明 |
| `manifest.json`、`CHECKSUMS.sha256` | 版本来源与逐文件校验 |
| `ACKNOWLEDGEMENTS.md` | 鸣谢 [@hairuiaa](https://github.com/hairuiaa) |

没有打入QQ账号资料、密码、访问Token、SSH密钥、聊天内容、服务器备份或原始日志。不是服务器磁盘克隆。**Docker基础镜像、QQ安装包、Node工具链不包含在ZIP中，首次构建需联网获取；不是完整离线镜像包。**

## 适用环境与快速开始

Linux x86_64 + Docker Engine/Compose v2 + Python3。Windows上需使用Linux容器环境/WSL2，不可直接运行Linux注入库。仅作独立实例安装；本包不自动改动任何已有服务器、账号或海豹连接。

解压后在项目根目录运行：

```sh
python3 deploy/init-config.py
# 输入自选WebUI密码；留空会生成密码并仅在你的本机显示。
docker compose config --quiet
docker compose build
docker compose up -d
```

打开本机 `http://127.0.0.1:3080/`，使用刚设置/生成的WebUI密码，再用独立测试QQ扫码。部署在远程服务器时先建立SSH本地转发：

```sh
ssh -N -L 3080:127.0.0.1:3080 USER@YOUR_SERVER
```

随后在运行SSH的电脑打开相同localhost地址。基础配置仅将WebUI3080和Milky5010绑定到服务器回环地址，PMHQ13000不公开。不要把localhost误当作其他电脑的地址。可选Nginx `/llbot/` 入口见 `deploy/nginx-llbot.example.conf`，样例仅监听回环8080，不会自动安装；保留WebUI认证，并包含当前构建登录后保持代理原地址的修复。

本包配置默认不自动重启（与本次部署保留策略一致）。机器重启后需手动启动；如后续决定自启，应先完成稳定性评估再明确调整restart策略。

## 接入海豹

本包不含海豹程序或插件。Milky默认在容器内5010启用，访问密钥由初始化脚本生成，保存在本机 `state/api-access.secret`，不在本包中预置。LLBot账户最终配置以WebUI显示为准。

- 同一Docker网络的海豹可使用 `http://llbot:5010/api`；容器名称仅在同一网络可解析。
- 宿主机服务可使用 `http://127.0.0.1:5010/api`。
- 不同服务器需要另行规划受保护的连接，不要把该示例直接换成无认证公网端口。
- 接入时填写Milky访问Token，而不是WebUI密码或平台注册Token。

本次新机海豹QQ连接原为停用，切换后保持停用，没有接管旧机业务。

## 构建、验证与后续维护

源码基于官方v8.3.2，Fork提交固定在manifest。重新构建LLBot：准备Node24与Python3，在source目录执行 `python3 selfhost/build.py --node /path/to/node`。该脚本仅构建控制端，不构建PMHQ原生组件；PMHQ本包没有原生源码。原验证208项测试通过，后端类型检查通过，前端生产构建通过；完整前端类型检查仍存在105项与上游一致的遗留错误，未宣称全部类型检查通过。

私聊文本、PNG、两节点合并记录有限双向测试已通过。新机已实际扫码在线，但群消息、并发、长期内存/句柄稳定性、全部媒体格式与全部kernel RPC未验证。1.5GiB内存上限曾出现限额回收压力而没有OOM，不能据此认定没有泄漏。新空白机器上的Docker配方只做静态/配置核验，不冒称已完整重建与扫码验收。详见 `docs/验证与限制.md`。

QQ版本与偏移必须配套，不能只修改版本号、下载地址或复用其他版本偏移。后续QQ版本策略可能改变，本包不承诺永久可登录。更新前备份并使用独立测试账号验证，可按 `docs/回滚与备份.md` 恢复。

## 来源与许可

- LLBot上游：https://github.com/LLOneBot/LuckyLilliaBot
- LLBot Fork：https://github.com/Qwssttcc/LLBot-selfhost/tree/selfhost/external-pmhq-v8
- PMHQ：https://github.com/linyuchen/PMHQ
- 原LLBot GPL-2.0版权/许可与依赖许可保留；PMHQ、QQ分别遵循各自条款，详见 `THIRD-PARTY-NOTICES.md`。

**特别鸣谢 [@hairuiaa](https://github.com/hairuiaa)。**
