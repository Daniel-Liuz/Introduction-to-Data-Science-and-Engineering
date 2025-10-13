# Midscene_Crawler

> 基于`playwright`和`midscene.js`自动化爬虫项目，给`Playwright`插上AI的翅膀，仅需1天，即可上手，核心是修改 xxx.spec.ts文件，使用各种封装好的ai函数，通过搭积木的方式，让计算机来为你模拟页面操作，轻松实现爬虫

__技术栈：__

* [plywright](https://github.com/microsoft/playwright) Web UI自动化测试工具。

* [midscene.js](https://github.com/web-infra-dev/midscene) 提供AI定位断言能力。

* [ai函数用法](https://midscenejs.com/zh/api.html) 提供AI函数，降低编写难度


## 安装与配置

1. 克隆项目到本地：

```shell
git clone https://github.com/Daniel-Liuz/Midscene_Crawler.git
```

2. 安装依赖

```shell
cd MIDSCENE_CRAWLER
npm install
```

3. 安装运行浏览器

```shell
npx playwright install
```

4. 配置大模型

> 本项目默认使用 `qwen-vl-max-latest` 模型,。如果想使用其他模型请参考midscenejs官方配置。

阿里云百练：https://bailian.console.aliyun.com/

使用其他模型：https://midscenejs.com/zh/model-provider.html

在 `.env` 文件中配置环境变量：

```ts
export OPENAI_API_KEY="sk-your-key"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export MIDSCENE_MODEL_NAME="qwen-vl-max-latest"
```

## 使用示例

在项目的`crawler`目录，附带了`esi_download.spec.ts`例子。

如果想跑下面这个示例，请先前往https://esi.clarivate.com完成注册

将用户名和密码分别替换下方的代码

## ai函数
在 Midscene 中，你可以选择使用自动规划（Auto Planning）或即时操作（Instant Action）。

agent.ai() 是自动规划（Auto Planning）：Midscene 会自动规划操作步骤并执行。它更智能，更像流行的 AI Agent 风格，但可能较慢，且效果依赖于 AI 模型的质量。

agent.aiTap(), agent.aiHover(), agent.aiInput(), agent.aiKeyboardPress(), agent.aiScroll(), agent.aiDoubleClick(), agent.aiRightClick() 是即时操作（Instant Action）：Midscene 会直接执行指定的操作，而 AI 模型只负责底层任务，如定位元素等。这种接口形式更快、更可靠。当你完全确定自己想要执行的操作时，推荐使用这种接口形式。

具体的ai函数和示例可以参照文件夹中的

ai_function.md

也可以前往api官网了解

https://midscenejs.com/zh/api.html

__示例代码__

```ts
import { test } from './fixture';

test('download esi data', async ({ page, ai, aiTap, aiInput, aiWaitFor,aiAction }) => {
 // 步骤 1: 导航到目标网站
  await page.goto('https://esi.clarivate.com');
  await aiWaitFor('界面加载成功', { timeoutMs: 100000 });
  await aiInput('此处替换为你的用户名', 'Email address input');
  await aiInput('此处替换为你的密码', 'Password input');
  await aiTap('Sign In button');


  // 步骤 2: 智能等待登录成功并加载主界面
  // 等待直到 "Top Papers by Institutions" 标题出现，表明已进入主界面
  await aiWaitFor('界面中包含 "Top Papers by Research Fields"', { timeoutMs: 500000 });

  // 步骤 3: 确保结果列表设置为 "Institutions"
  // 这是一个保险步骤，通常默认就是这个选项
  await aiTap('点击Result lists下方的“Research Fields”选择框');
  await aiTap('选择“Institutions”选项');

  // 步骤 4: 获取单个CASE

  await aiTap('the "Add Filter" link');
  await aiTap('the "Research Fields" link');
  await aiTap('Agricultural Sciences的+号'); 
  await aiTap('Indicators那一行的第一个按钮下载数据');
  await aiTap('点击"CSV"');
  await aiWaitFor('界面中包含 "Top Papers by Institutions"', { timeoutMs: 100000 });
  });
```


__运行测试__

测试全部代码

```shell
npx playwright test
```

```shell
npx playwright test crawler/esi_download.spec.ts

```

__测试报告__
测试报告会被保存在midscene_run的文件夹下方
效果如文件夹中的“回放示例.html”

# 相关资料和链接
## 📄 资源 

* 官网和文档: [https://midscenejs.com](https://midscenejs.com/zh)
* API 文档: [https://midscenejs.com/zh/api.html](https://midscenejs.com/zh/api.html)
* GitHub: [https://github.com/web-infra-dev/midscene](https://github.com/web-infra-dev/midscene)

## 🤝 社区

* [Web Infra 团队微信公众号](https://lf3-static.bytednsdoc.com/obj/eden-cn/vhaeh7vhabf/web-infra-wechat.jpg)
* [飞书交流群](https://applink.larkoffice.com/client/chat/chatter/add_by_link?link_token=291q2b25-e913-411a-8c51-191e59aab14d)
* [Discord](https://discord.gg/2JyBHxszE4)
* [Follow us on X](https://x.com/midscene_ai)

  <img src="https://github.com/user-attachments/assets/211b05c9-3ccd-4f52-b798-f3a7f51330ed" alt="lark group link" width="300" />

# 致谢
本项目是基于字节的开源项目Midscene的二次开发，旨在利用其AI和Playwright的能力，大幅降低爬虫过程中的配置和编写代码的难度。只要给出一个网站，可以在1天的时间里，就可以完成对其的爬取！

Midscene的源代码：https://github.com/web-infra-dev/midscene