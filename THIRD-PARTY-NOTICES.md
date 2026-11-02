# 第三方组件与许可

- LLBot Fork：基于 LuckyLilliaBot v8.3.2；GPL-2.0，原版权与完整 LICENSE 随源码和运行文件保留。源码提交见 manifest.json。
- PMHQ 7.3.2：本包附官方发布的 x86_64 可执行程序和注入库，未修改原生二进制；本包没有它们的可重建原生源码，也不为这些二进制新增或推定开源许可。原项目 https://github.com/linyuchen/PMHQ 。进一步分发前应核实原作者授权及适用条款。
- QQ Linux：腾讯产品；安装包不在本包中，Docker构建通过固定URL获取并校验摘要。QQ客户端不适用LLBot的GPL许可。
- Node.js、依赖包、容器基础系统：适用各自许可证，runtime/node_modules 保留随包许可。Docker基础镜像不包含在本压缩包中。

特别鸣谢 **[@hairuiaa](https://github.com/hairuiaa)**。
