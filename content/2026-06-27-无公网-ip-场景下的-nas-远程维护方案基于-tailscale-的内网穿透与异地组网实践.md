---
title: "无公网 IP 场景下的 NAS 远程维护方案：基于 Tailscale 的内网穿透与异地组网实践"
slug: "无公网-ip-场景下的-nas-远程维护方案基于-tailscale-的内网穿透与异地组网实践"
date: 2026-06-27
status: desensitized
feishu_token: "C6qDwGRh0ivDIUkgTcmc6U8HnRf"
feishu_obj_token: "PfIydH8T8oRjDZxmBnTcqOwonIg"
tags: []
categories: []
publish:
  github: null
  wechat: null
  csdn: null
---
desensitized_at: 2026-06-27 11:07
## 一、问题背景

当前使用场景如下：

```Plain Text
本地电脑：Windows
远程设备：某品牌NAS NAS
访问方式：通过 my某品牌NAScloud 远程进入 NAS 管理界面
虚拟机：某品牌NAS Virtualization Station 中运行 Ubuntu
网络条件：NAS 所在网络没有公网 IP
核心目标：远程稳定管理 Ubuntu 虚拟机，便于后续部署 Docker、开发工具和其他服务
```

实际遇到的问题包括：

```Plain Text
1. 某品牌NAS 虚拟机网页控制台无法稳定复制粘贴命令；
2. 长期依赖网页控制台操作效率低，容易出错；
3. NAS 所在网络没有公网 IP，外部无法直接访问 Ubuntu 虚拟机；
4. 需要建立一条安全、稳定、可长期使用的远程运维通道；
5. 后续希望通过 Windows Terminal / PowerShell 直接 SSH 到 Ubuntu。
```

因此，当前问题的本质不是单纯的“命令无法粘贴”，而是：

> 在无公网 IP 的 NAS 网络环境下，如何安全、稳定地进入 NAS 所在网络，并远程维护 Ubuntu 虚拟机。

---

## 二、技术定位：这属于内网穿透还是 VPN？

从使用效果看，这属于：

```Plain Text
内网穿透 / NAT 穿透 / 异地组网 / 远程运维通道建设
```

但需要区分两类方案。

传统内网穿透通常是：

```Plain Text
公网地址:端口 → 内网设备:端口
```

例如把内网 Ubuntu 的 SSH 映射成公网端口，然后外部通过公网地址访问。

而 Tailscale 的方式不是简单暴露某个端口，而是把多台设备加入同一个私有虚拟网络：

```Plain Text
Windows 电脑
某品牌NAS NAS
Ubuntu 虚拟机
手机
其他设备
```

加入后，每台设备会获得一个 Tailscale 虚拟 IP，通常是：

```Plain Text
100.x.x.x
```

![图片展示的是Tailscale管理界面，显示了已连接的两台设备信息。设备一为“我的设备”，地址为[Tailscale IP]，操作系统为Windows 11 25H2，状态为Connected；设备二为“ubuntu-openclaw”，地址为[Tailscale IP]，操作系统为Linux 6.8.0-117-generic，同样状态为Connected。界面顶部有Machines、Apps等导航栏，右上角有“Add device”按钮。该图片与文档中介绍Tailscale方式解决无公网IP设备互联问题的内容相关，直观呈现了加入Tailscale网络后的设备管理情况。]([内部链接]

设备之间可以像在同一个局域网中一样互相访问。

因此，更准确的说法是：

> Tailscale 是一种基于 WireGuard 的安全异地组网工具，通过 NAT 穿透能力解决无公网 IP 设备之间的互联问题。

---

## 三、为什么推荐 Tailscale

在 NAS 所在网络没有公网 IP 的情况下，Tailscale 的优势非常明显：

```Plain Text
1. 不需要公网 IP；
2. 不需要路由器端口转发；
3. 不需要把 SSH 暴露到公网；
4. Windows、NAS、Ubuntu 可以加入同一个虚拟内网；
5. 可以直接通过设备名或 100.x.x.x 地址 SSH 到 Ubuntu；
6. 后续可以按需扩展为访问整个 NAS 所在局域网。
```

对于当前场景，目标链路应从：

```Plain Text
Windows 浏览器 → my某品牌NAScloud → 某品牌NAS 网页控制台 → Ubuntu
```

调整为：

```Plain Text
Windows Terminal / PowerShell → Tailscale → Ubuntu SSH
```

这样后续复制粘贴、脚本执行、文件传输、Docker 操作都会方便很多。

---

## 四、推荐整体架构

当前阶段推荐最小可用架构：

```Plain Text
Windows 电脑
    │
    │ Tailscale
    │
Ubuntu 虚拟机
    │
    └── SSH 运维入口
```

后续如果需要访问 NAS 或 NAS 所在局域网中的其他设备，再扩展为：

```Plain Text
Windows 电脑
    │
    │ Tailscale
    │
Ubuntu 虚拟机 / 某品牌NAS NAS
    │
    │ 可选：Subnet Router
    │
NAS 所在局域网
```

初期不要急着配置 Subnet Router，先完成最关键的 SSH 运维闭环。

---

## 五、实施步骤

打开官网（https://tailscale.com/），点击右上角「Sign up」，推荐用 Google、Microsoft 账号授权登录（无需注册新账号，减少密码泄露风险），也可使用邮箱注册（务必设置强密码，包含大小写、数字、特殊符号）。

### 第一步：Windows 安装并登录 Tailscale

- 在 Windows 电脑上安装 [Tailscale 客户端](https://tailscale.com/download/windows)，然后登录账号。
- 登录成功后，Windows 会加入你的 Tailscale 虚拟网络。
- 在 PowerShell 中执行：

```PowerShell
tailscale status
```

如果能看到当前 Windows 设备，说明连接成功。

---

### 第二步：Ubuntu 虚拟机开启 SSH

由于当前还需要通过 某品牌NAS 网页虚拟机控制台操作 Ubuntu，所以先手动输入下面几行：

```Bash
sudo apt update
sudo apt install -y openssh-server curl ca-certificates
sudo systemctl enable --now ssh
```

确认 SSH 服务状态：

```Bash
systemctl status ssh
```

查看 Ubuntu 当前 IP：

```Bash
hostname -I
```

这一步的目的是先确保 Ubuntu 具备 SSH 登录能力。

---

### 第三步：Ubuntu 安装 Tailscale

在 Ubuntu 中执行：

```Bash
curl -fsSL https://tailscale.com/install.sh | sh
```

启动 Tailscale：

```Bash
sudo systemctl enable --now tailscaled
sudo tailscale up --hostname=ubuntu-openclaw
```

执行后，终端通常会输出一个登录链接。

在浏览器中打开该链接，并使用同一个 Tailscale 账号授权，Ubuntu 就会加入你的 Tailscale 网络。

---

### 第四步（可跳过）：如果网页控制台不方便复制链接，使用 Auth Key

如果 某品牌NAS 网页控制台无法复制 Tailscale 登录链接，可以在 Tailscale 管理后台生成一次性 Auth Key。

然后在 Ubuntu 中执行：

```Bash
sudo tailscale up --auth-key=tskey-auth-你的密钥 --hostname=ubuntu-openclaw
```

建议：

```Plain Text
1. 使用一次性 Auth Key；
2. 设置较短有效期；
3. 不要把 Auth Key 发给别人；
4. 用完后可以在 Tailscale 后台吊销。
```

---

### 第五步：Windows 通过 Tailscale SSH 到 Ubuntu

在 Windows PowerShell 中执行：

```PowerShell
tailscale status
```

如果看到类似：

```Plain Text
100.x.x.x    ubuntu-openclaw
```

![图片展示了在Windows PowerShell中执行SSH命令后，成功登录Ubuntu 24.04.3 LTS系统的界面。界面上显示了Ubuntu系统的系统信息，如系统负载、内存使用率等，还列出了IPv4和IPv6地址。下方有系统更新提示，可立即应用61个更新。登录成功后，用户可在Windows Terminal/PowerShell中操作Ubuntu，不再依赖某品牌NAS网页虚拟机控制台，与上文介绍的Windows通过Tailscale SSH到Ubuntu的内容相呼应。]([内部链接]

就可以直接 SSH：

```PowerShell
ssh 技术负责人@ubuntu-openclaw
```

或者使用 Tailscale IP：

```PowerShell
ssh 技术负责人@100.x.x.x
```

登录成功后，后续就可以直接在 Windows Terminal / PowerShell 中操作 Ubuntu，不再依赖 某品牌NAS 网页虚拟机控制台。

---

## 六、在 某品牌NAS NAS 上安装 Tailscale（可跳过，需要在局域网环境下操作）

如果要在 某品牌NAS 上安装 Tailscale，可以在 某品牌NAS 管理界面中：

```Plain Text
App Center → 搜索 Tailscale → 安装 → 打开 → 登录同一个账号 → Connect
```

安装完成后，NAS 本身也会成为 Tailscale 网络中的一台设备，可以通过 Tailscale IP 或设备名访问。

---

## 七、是否需要配置 Subnet Router？

初期不建议配置。当前目标只是：

```Plain Text
Windows → Tailscale → Ubuntu SSH
```

这不需要 Subnet Router。

只有当你后续需要访问 NAS 所在局域网中的其他设备时，才需要考虑 Subnet Router。

例如需要访问：

```Plain Text
NAS 管理地址：[内部地址]
Ubuntu 局域网地址：[内部地址]
路由器地址：[内部地址]
```

这时可以让 Ubuntu 或 某品牌NAS 作为 Subnet Router，把整个局域网网段暴露给 Tailscale 网络。

假设 NAS 所在局域网是：

```Plain Text
[内部地址]/24
```

在 Ubuntu 中开启 IP 转发：

```Bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

发布局域网路由：

```Bash
sudo tailscale set --advertise-routes=[内部地址]/24
```

然后进入 Tailscale 管理后台批准该路由：

```Plain Text
Machines → ubuntu-openclaw → Route settings → Approve [内部地址]/24
```

但这属于后续增强功能，不建议一开始就做。

---

## 八、连接验证方法

## 查看设备列表

在 Windows 或 Ubuntu 上执行：

```Bash
tailscale status
```

可以看到当前 tailnet 中的设备列表。

---

## 测试 Tailscale 连通性

```Bash
tailscale ping ubuntu-openclaw
```

如果能 ping 通，说明 Tailscale 网络正常。

---

## 测试 SSH

```PowerShell
ssh 技术负责人@ubuntu-openclaw
```

或者：

```PowerShell
ssh 技术负责人@100.x.x.x
```

如果可以登录 Ubuntu，说明远程运维链路已经打通。

---

## 九、安全建议

建议遵循以下原则：

```Plain Text
1. 不把 SSH 22 端口暴露到公网；
2. Tailscale 账号开启 MFA / 两步验证；
3. Auth Key 使用一次性、短有效期；
4. 不使用的设备及时从 Tailscale 后台移除；
5. 初期不启用 Exit Node；
6. 初期不启用 Subnet Router；
7. 后续 SSH 建议改为 SSH Key 登录；
8. NAS 管理后台不要直接暴露到公网；
9. 只让可信设备加入自己的 tailnet；
10. 定期更新 Tailscale 客户端和 Ubuntu 系统补丁。
```

---

## 十、当前推荐落地顺序

建议按照下面顺序执行：

```Plain Text
第一步：Windows 安装并登录 Tailscale；
第二步：Ubuntu 安装 openssh-server；
第三步：Ubuntu 安装并登录 Tailscale；
第四步：Windows 使用 tailscale status 确认能看到 Ubuntu；
第五步：Windows 通过 ssh 技术负责人@ubuntu-openclaw 登录 Ubuntu；
第六步：成功后停止依赖 某品牌NAS 网页虚拟机控制台；
第七步：后续再继续安装 Docker、开发工具和其他服务；
第八步：如需访问整个 NAS 局域网，再配置 Subnet Router。
```

---

## 十一、最终结论

当前场景可以归类为：

```Plain Text
无公网 IP 环境下的内网穿透 / 异地组网 / 远程运维通道建设
```

但更准确地说，推荐方案不是传统端口映射型内网穿透，而是：

```Plain Text
基于 Tailscale 的安全虚拟局域网
```

最推荐的最终链路是：

```Plain Text
Windows Terminal / PowerShell
        ↓
Tailscale
        ↓
Ubuntu SSH
```

一句话总结：

> 先用 Tailscale 打通 Windows 到 Ubuntu 的远程 SSH 运维链路，替代 某品牌NAS 网页虚拟机控制台；等远程操作稳定后，再继续处理 Docker、开发环境、代理出口等后续问题。