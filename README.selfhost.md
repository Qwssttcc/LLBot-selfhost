# LLBot 历史版自托管候选分支

本地分支 `selfhost/no-platform-registration` 基于官方 **v7.12.15**（`e0d5d2067651b0e526c841addaa3b7de51d2dd8c`），版本标识为 `7.12.15-selfhost.1`。保留原作者署名与 GPL-2.0 许可证。

## 已完成与边界

- 选用尚未包含 LLBot 平台注册流程的历史源码，未修改 v8 的第三方签名服务或绕过其账号授权。
- 固定官方历史 PMHQ Linux x64 **7.3.2** 的下载地址、归档 SHA256、两个原始二进制的 SHA256；不使用 `latest`，不修改二进制。
- 前端依赖锁文件已按源码重新生成。源码构建与原仓库 157 项单元测试通过，包含 WebUI 认证测试。
- **尚未进行真实 QQ 登录、消息收发或当前 QQ 客户端兼容性验证。** 二进制中未检出已知认证字符串，只是静态证据，不能证明运行中完全无外部依赖。
- 这不是 v8.2.1 的功能等价替代，也不是全部组件均能从开源源码重建的实现。PMHQ 原生部分仍为官方预编译历史二进制；其二进制未提交到本仓库。
- 新旧服务器均未部署或修改。没有导入 QQ 会话、密码、平台注册 Token 或生产配置。

## 从源码构建

需要 Python 3.11+、Node.js **24.x**，以及访问公开 npm Registry 的网络。工具版本和归档校验值见 `selfhost/manifest.json`。

```sh
python selfhost/build.py
# Windows 可显式指定 Node 路径：
python selfhost/build.py --node "C:/path/to/node.exe"
```

此命令校验并获取 Yarn 4.14.1 和 pnpm 11.25.0，按锁文件安装依赖（禁用安装脚本），构建后端/WebUI并运行隔离测试。产物位于 `dist/`，执行记录为 `selfhost/build-report.json`。该命令不会启动 QQ、部署或发送消息。

如要获取用于独立兼容性测试的原版 PMHQ：

```sh
python selfhost/prepare.py --pmhq
```

输出在 `selfhost/native/linux-x64/`；下载文件校验不符即失败。**此命令仅下载，不启动**。需要另行准备匹配的 Linux QQ 客户端、独立数据目录和实际登录验证，不能把 PMHQ 9.x 的原平台注册 Token 填入旧版来宣称兼容。

## 运行与认证

LLBot 应连接同机或隔离私有网络内的 PMHQ，使用原参数：

```sh
cd dist
node llbot.js --pmhq-host=127.0.0.1 --pmhq-port=13000
```

以上只是已有 PMHQ 实例的 LLBot 启动方式，不会替你启动 QQ。不要直接指向生产 PMHQ；先用独立账号和数据目录验证。

**保留 WebUI 登录密码及 Milky / OneBot / Satori 的本地访问令牌。** “无需平台注册”不意味着公开管理接口或消息 API 可以免认证。默认 WebUI 仍监听 127.0.0.1，Milky默认关闭。

仓库原来的云镜像发布及依赖真实 QQ 的端到端工作流已在 `.github/workflows/` 改为 `.yml.disabled` 后缀留存，避免 Fork 后误向原项目发布。原 `script/install-llbot-docker.sh` 会查询最新版本，**不适用于本分支**。本分支不提供未经验证的生产一键部署或自动更新。

## 后续验收

1. 独立环境确认 QQ 登录不需要 LLBot 平台注册，记录 PMHQ 与 QQ 的确切版本。
2. 验证文本、图片、群/私聊收发、Milky 历史消息/合并转发和自主AI所需 API，检查失败返回及回执语义。
3. 持续观察超时、掉线和资源；少量成功消息不能证明稳定兼容。
4. 只有测试通过后再决定新机部署。旧机数据与在线服务保持不动。

GitHub Fork：https://github.com/Qwssttcc/LLBot-selfhost 。兼容候选使用 `selfhost/no-platform-registration` 分支；`main` 是上游新版基线，不能将其当作无需平台注册的实现。

官方依据：
- https://github.com/LLOneBot/LuckyLilliaBot/releases/tag/v7.12.15
- https://github.com/LLOneBot/LuckyLilliaBot/tree/e0d5d2067651b0e526c841addaa3b7de51d2dd8c
- https://www.npmjs.com/package/pmhq-dist-linux-x64/v/7.3.2
- https://github.com/linyuchen/PMHQ
