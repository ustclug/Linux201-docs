# 安全

!!! warning "本文初稿编写中"

## 「安全」是什么？

## 攻击方视角：常见安全问题简介

## 防守方视角：如何防御攻击

### 教训

#### 保护个人计算机的安全

!!! example "新闻选摘：SSH 软件与后门"

    [Putty、Winscp等汉化版软件内置后门事件 上万服务器账户泄露](http://yangjunwei.com/742.html)

    > 经安全厂商证实，部分汉化版PuTTY、WinSCP、SSH Secure等开源软件存在后门程序，可能导致Linux服务器系统管理员密码及资料泄露。有知情人士透露，截至目前，PuTTY后门服务器受害账户已达到1万多，且仍在持续增加。
    >
    > …………其中PuTTY从没有官方中文版，而WinSCP已经拥有官方中文版。最近有Linux服务器管理员发现，上述工具的非官方“汉化版”疑似内置后门，部分网站和企业服务器已因此遭到黑客攻击，导致系统root密码泄漏以及资料泄漏。
    > 
    > …………PuTTY等软件本身是开源的，汉化版属于“被人动了手脚”，安全性往往难以保障。

    [Trojanized versions of PuTTY utility being used to spread backdoor](https://arstechnica.com/information-technology/2022/09/trojanized-versions-of-putty-utility-being-used-to-spread-backdoor/)

    > Researchers believe hackers ... have been pushing a Trojanized version of the PuTTY networking utility in an attempt to backdoor the network of organizations they want to spy on.
    >
    > ...at least one customer it serves had an employee who installed the fake network utility by accident...

    ---

    总结：**请永远从官网（以及其他可信的渠道）下载运维类软件，并且永远不要碰诸如「破解」「汉化」版本的运维软件**。
    <span style="color: red">做不到这一点的运维应当被立刻开除。</span>

!!! example "新闻选摘：LastPass 与 Plex"

    背景：LastPass 是一款免费的在线密码管理器，曾经出现过[多次安全事件](https://en.wikipedia.org/wiki/LastPass#Security_incidents)；Plex 是一款家庭媒体服务器软件。

    [Lastpass事件追踪：黑客利用Plex漏洞窃取了核心工程师的主密码](https://www.landiannews.com/archives/97510.html)

    > Lastpass 终于又公布了被黑的调查进展，本次更新的调查报告指出：Lastpass 一名核心工程师的家庭办公电脑遭到黑客的入。**这还涉及了另外一款知名软件：流媒体软件 Plex。**
    > 
    > …………
    > 
    > 最初黑客应该是已经瞄准 Lastpass 的这名核心工程师，该工程师是 Lastpass 四名掌握 DevOps 解密密钥的工程师之一。
    >
    > **黑客通过 Plex 存在的远程代码执行漏洞**，在这名核心工程师的家庭办公电脑上安装了键盘记录器，工程师登录 DevOps 时，输入解密密钥 (相当于主密码) 的时候键盘记录器成功窃取了主密码。

    [Plex急忙解释：Lastpass被黑与他们无关 2年前的漏洞都不修复](https://www.landiannews.com/archives/97690.html)

    > 搞笑的是 Plex 现在站出来回应表示自己不背锅，因为被黑的 Lastpass 工程师两年多都没有更新自己的 Plex 软件，也就是长期使用带有安全漏洞的版本。
    >
    > Plex 称 2020 年 5 月 7 日该公司披露了一个安全漏洞，该漏洞允许那些有权限访问服务器管理员 Plex 账户的人，通过相机上传功能上传恶意文件到媒体库，然后利用服务器数据目录的位置与上传的库重叠，并让媒体服务器自动执行这个恶意文件。
    >
    > **披露漏洞的当天 Plex 就推出了 Plex Media Server v1.19.3 版修复了该漏洞，然后至少到 2022 年 8 月 Lastpass 工程师都没有升级自己的软件。**

    ---

    总结：**保证自己安装的操作系统与应用安装了最新的安全更新，并且避免继续使用已经结束支持的软件。**
    [endoflife.date](https://endoflife.date/) 整理了一些软件的支持周期，可以作为参考。

!!! example "真实案例：为什么不能随意下载破解软件"

    小 A 是一名学生，因为研究领域的需要，需要使用某款付费的 CAD 软件。
    TA 先前因为自己写的程序经常被报毒，因此关闭了杀毒软件。
    搜索后，TA 在 GitHub 上找到了一个仓库，似乎是破解版：

    ![GitHub 仓库](../images/security-example-github-malware.png)

    安装后似乎一切正常，但是几天之后，TA 发现自己的 GitHub 账号 star 了奇怪的仓库，并且创建了一个诡异的仓库，内容为热门游戏「幻兽帕鲁」的破解版。TA 感觉很诧异，因为自己的 GitHub 账号早已开启了两步验证（2FA）！

    检查 [Security Log](https://github.com/settings/security-log) 后发现，在一天前，有一个来自英国的 IP 使用 Windows Chrome「切换」了自己在 Windows 浏览器中的 session 的国家，但是 TA 没有在 Windows 下使用过 Chrome。在出问题的当天下午，另一个来自乌克兰的 IP 使用一个 Python 脚本执行了一系列操作，包括创建了那个奇怪的仓库。**由于攻击者直接偷取了浏览器的 session，因此非敏感操作（例如创建仓库）不会触发两步验证。**

    在设置中的 [Sessions](https://github.com/settings/sessions) 页面移除了其他的 session 之后，TA 检查了自己的电脑，开始怀疑这个「破解软件」。将安装包的 zip 上传至 [VirusTotal](https://virustotal.com) (1) 后，发现这个安装包会执行各种可疑行为，例如从网络下载其他可执行程序并运行、将自己加入 Windows Defender 的白名单等。
    {: .annotate }

    1. VirusTotal 是一个可以上传文件进行多引擎扫描的网站（包括国际与国内的知名杀毒软件），并且还会通过沙盒运行文件，查看其行为。VirusTotal 是安全研究人员的常用工具之一。

    进一步分析发现，这个压缩包仅仅只是个恶意软件下载器：它会从 Pastebin 服务 (1) 获取恶意软件的下载链接，下载后运行。而运行的恶意软件又会从攻击者创建的 Steam 的个人页面与 Telegram 频道获取攻击指令：
    {: .annotate }

    1. Pastebin 是一个文本分享服务，用户可以在上面分享文本、代码等。由于其匿名性，也经常被用于分享恶意软件的配置文件、下载链接等。

    ![Steam Community](../images/security-example-steam-malware.png)

    于是 TA 的机器就这样沦陷了。

    ---

    总结：**不要随便关杀毒软件、跑破解程序；就算真的不得不要也请务必在虚拟机里面运行。**
