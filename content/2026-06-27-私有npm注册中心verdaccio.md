---
title: "私有npm注册中心——Verdaccio"
slug: "私有npm注册中心verdaccio"
date: 2026-06-27
status: desensitized
feishu_token: "XU8iwhaiwiZxAzkHhc1crf3jnTf"
feishu_obj_token: "LvWqd6m3Vo64hkxbYvMcYThsndh"
tags: []
categories: []
publish:
  github: null
  wechat: null
  csdn: null
---
desensitized_at: 2026-06-27 11:07
某开源库第三方库无npm包，需要搭建私有npm注册中心。

**1.搭建npm注册中心**

在NAS上基于docker实现，参考[https://verdaccio.org/zh-CN/docs/docker](https://verdaccio.org/zh-CN/docs/docker)，服务地址为：[http://[内部地址]/](http://[内部地址]/)。

需要在nas上配置好相关权限。

Verdaccio Docker镜像启动成功后的界面如下：

![图片展示的是Verdaccio私有npm注册中心的]([内部链接]

**2.创建用户**

在git bash中输入如下命令，创建用户：

npm adduser --registry http://[内部地址]/



## 用户信息

# zhijie.wu/Share123

**3.登录 Verdaccio**

# 模板

npm login --registry=http://ip:4873

# 或者

npm login --registry http://localhost:4873/

# 测试

npm login --registry=http://[内部地址]

![图片展示了在git bash中登录私有npm注册中心的操作界面。命令为“npm login --registry http://[内部地址]/”，执行后显示“Log in on http://[内部地址]/”，并提示输入用户名和密码。下方显示“Logged in on http://[内部地址]/。”。该图片与文档中“登录Verdaccio”部分对应，直观呈现了登录操作的执行过程及结果。]([内部链接]

**4.发布npm包**

进入到npm包所在的根目录，在git bash中输入如下命令

 npm publish --registry http://[内部地址]/

发布成功的提示如下

![图片展示的是在git bash中发布npm包后的提示信息。显示npm包“electron-vite-template”发布成功，版本为1.0.0，大小为910.8 KB，文件总数为74个，还列出了文件名、大小、sha512等信息。发布地址为“http://[内部地址]/”，并带有“latest”和“default access”标签。该图片与文档中“发布npm包”步骤对应，直观呈现了发布成功的提示内容。]([内部链接]

**5.安装npm包**

有两种方式，参见：[https://verdaccio.org/docs/setup-npm](https://verdaccio.org/docs/setup-npm)

# 进入项目根目录后，在git bash中输入如下命令设置注册地址，生成.npmrc文件

npm set registry http://[内部地址]/ --location project

# 只在单独的安装命令中使用私有注册中心

npm install lodash --registry http://[内部地址]

1. **删除已上传npm包**

在git bash中执行如下命令，可删除指定的项目（yourPackage为你的项目名称）

# 模板

npm unpublish --force yourPackage --registry http://localhost:4873

# 测试

\$ npm unpublish --force test2 --registry http://[内部地址]

![图片展示了在git bash中删除已上传npm包的操作示例。命令为“npm unpublish --force test2 --registry http://[内部地址]”，执行后显示“npm warn using --箭步骤的内容。这些内容属于。]([内部链接]

1. **删除用户**