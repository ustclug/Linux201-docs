---
icon: octicons/device-desktop-16
---

# Linux 桌面与窗口系统

!!! note "主要作者"

    [@taoky][taoky]

!!! warning "本文编写中"

!!! note "参考"

    本章参考了以下内容：
    
    - [@libreliu][libreliu] 在 [2024 年 4 月 21 日 USTCLUG 的小聚「Linux 图形堆栈初探」](https://ftp.lug.ustc.edu.cn/weekly_party/2024.04.21_Linux_Graphics_Journey/)。
    - [farseerfc](https://github.com/farseerfc) 有关[桌面系统混成器](https://farseerfc.me/zhs/brief-history-of-compositors-in-desktop-os.html)的介绍。
    - [@iBug][iBug] 的 [VNC 相关配置](https://wiki.ibugone.com/external/vserver/)。

相比于久负盛名的 Windows 与 macOS，Linux 的桌面以及其生态是独特的。本文将简单介绍 Linux 桌面与窗口系统中一些重要的概念。

## X

以下未特殊标明的情况下，X11 协议均使用 Xorg 这个目前最主流的 X 实现。

!!! tip "部分内容在主章节中有介绍"

    如果你想知道怎么进行 SSH X Forwarding，以及如何在容器中运行 X 程序，可以参考[容器章节中的相关内容](../ops/virtualization/container.md#docker-gui)。

### 客户端、服务端与窗口 {#client-server-window}

X 窗口系统起源于 1984 年。在那个时代，桌面环境没有酷炫的效果，相比之下，性能与资源占用重要得多。并且当时个人计算机还是一个新兴的概念，用户更多的时候需要使用终端机连接到服务器上运行任务。因此，X 的设计上包含了当时那个年代设计的局限性，并且有着独特的「网络透明性」的设计：需要显示窗口的程序（客户端）和可以给用户显示窗口的程序（服务端）是可以分离的，通过网络去连接。对于单机场景，这里的「网络」大部分时候是 UNIX socket，而在诸如 SSH X Forwarding 这种通过网络连接的场合则是 TCP socket。

默认情况下，如果你正在使用 Linux 桌面，那么默认连接到的 socket 则为 `/tmp/.X11-unix/X0`（对应环境变量 `DISPLAY=:0`）。

!!! warning "X 的抽象套接字支持"

    Linux 支持「抽象套接字」（abstract socket），即允许 Unix socket 绑定到一个不在文件系统中的地址（正常的 Unix socket 需要将地址设置为一个文件路径）。在编写代码时，将 `bind()` 路径（`sun_path`）的开头设置为 `NULL` 就表示抽象套接字。可以查看 `/proc/net/unix` 文件，其中以 `@` 开头的条目则是抽象套接字。

    可以注意到，默认情况下，X 服务端会同时监听 `/tmp/.X11-unix/X0` 和 `@/tmp/.X11-unix/X0`：

    ```console
    $ cat /proc/net/unix | grep X11-unix/X0
    000000002c61e829: 00000003 00000000 00000000 0001 03 379918 @/tmp/.X11-unix/X0
    （省略）
    0000000055982f40: 00000002 00000000 00010000 0001 01 20744 /tmp/.X11-unix/X0
    （省略）
    ```

    X 在 2008 年引入这个特性时的[相关说明](https://cgit.freedesktop.org/xorg/lib/libxtrans/commit/Xtranssock.c?id=2afe206ec9569e0d62caa6d91c3fb057b0efa23d)如下：

    ```
    Unlike normal unix sockets, the abstract namespace is not bound to the
    filesystem.  This has some notable advantages; /tmp need not exist, the
    socket directory need not have magic permissions, etc.  xtrans servers
    will listen on both the normal and abstract socket endpoints; clients
    will attempt to connect to the abstract socket before connecting to the
    corresponding filesystem socket.
    ```

    所以事实上，上文的描述是有一些偏差的——目前 X 客户端仍然会会优先连接 `@/tmp/.X11-unix/X0`。

    抽象套接字在如今带来了一些安全性的挑战，因为和文件系统上的 `/tmp/.X11-unix/X0` 可以依靠文件级别的权限控制不同，抽象套接字只能通过网络命名空间实现隔离。但是如果直接关闭 X server 的抽象套接字，攻击者可以创建虚假的名为 `@/tmp/.X11-unix/X0` 的套接字，欺骗 X 客户端连接。不过连接到 X server 还需要经过一层认证机制（XAuthority），因此如果不去 `xhost +` 的话，攻击者必须要能够获取 XAuthority 信息，才能够连接到对应的 X server。

!!! tip "启动一个新的 X Server"

    存在这样一种场景：你需要启动一个独立的 X server 来测试，而不希望对应的程序使用当前的 X server。其中一个便利的工具是 `xvfb-run`：Xvfb 是一个无头（无显示）的 X server，对自动化测试场景来说很方便。安装 `xvfb` 包后，即可使用：

    ```shell
    xvfb-run -f xvfb-auth -n 99 xeyes
    ```

    这里我们设置 `XAUTHORITY` 文件为 `xvfb-auth`，并且 `DISPLAY` 为 `:99`。关于 `XAUTHORITY`，请参考[容器部分的介绍](../ops/virtualization/container.md#docker-gui)。然后可以通过以下命令确认：

    ```console
    $ DISPLAY=:99 XAUTHORITY=./xvfb-auth xlsclients 
    examplehost  xeyes
    ```

    如果希望创建一个 X server 并且能够以子窗口的形式显示出来，那么可以考虑使用 Xephyr 或者 Xwayland 来创建。以 Xephyr 为例，以下命令可以创建一个 800x600 的 X server，并且以窗口的形式显示：

    ```shell
    Xephyr :123 -ac -screen 800x600
    ```

    其他应用可以直接用 `DISPLAY=:123` 环境变量连接到这个 server。在 Wayland 环境下，也可以使用 `xwayland-run`，以 Xwayland 的 "rootful" 模式运行一个新的 X server。

可以运行 `xlsclients` 获取连接到当前 X 服务器的客户端列表：

```console
$ xlsclients
examplehost gsd-xsettings
examplehost steamwebhelper
examplehost code
examplehost mutter-x11-frames
examplehost steam
```

客户端可以创建一个或多个窗口，可以使用 `xwininfo` 获取窗口信息：

```console
$ xwininfo -root -tree

xwininfo: Window id: 0x503 (the root window) (has no name)

  Root window id: 0x503 (the root window) (has no name)
  Parent window id: 0x0 (none)
     57 children:
     0x1a00004 "desktop.md - Linux201-docs - Visual Studio Code": ("code" "Code")  1920x1200+306+1440  +306+1440
        1 child:
        0x2200007 (has no name): ()  1920x1200+0+0  +306+1440
（以下省略）
```

反直觉的是，这里「窗口」的概念可能比你想象的要广得多——在传统的 X11 应用程序中，很多小控件（例如按钮、输入框）也都是窗口。可以尝试打开一个比较复杂的传统 X 程序（例如 `xedit`），然后 `xwininfo` 看一下：

![xedit window](../images/xedit.png)

xedit 的界面
{: .caption }

```console
$ xwininfo -name xedit -tree

xwininfo: Window id: 0x4200072 "xedit"

  Root window id: 0x9cf (the root window) (has no name)
  Parent window id: 0x3800096 (has no name)
     1 child:
     0x4200073 (has no name): ()  590x440+0+0  +959+143
        6 children:
        0x4200099 (has no name): ()  8x8+572+436  +1531+579
        0x420007b (has no name): ()  8x8+572+84  +1531+227
        0x420007c (has no name): ()  590x351+0+89  +959+232
           4 children:
           0x420008a (has no name): ()  8x8+586+333  +1545+565
           0x420008c (has no name): ()  1x1+0+0  +959+232
              6 children:
              0x4200096 (has no name): ()  179x21+0+0  +960+233
                 2 children:
                 0x4200098 (has no name): ()  85x17+2+2  +963+236
                 0x4200097 (has no name): ()  64x17+87+2  +1048+236
              0x4200094 (has no name): ()  100x18+0+0  +960+233
                 1 child:
                 0x4200095 (has no name): ()  14x4+-1+-1  +960+233
              0x4200093 (has no name): ()  8x8+0+0  +960+233
              0x4200092 (has no name): ()  64x17+0+0  +960+233
              0x420008e (has no name): ()  1x1+0+0  +960+233
                 2 children:
                 0x4200091 (has no name): ()  14x1+-1+-1  +960+233
                 0x420008f (has no name): ()  1x1+15+0  +976+234
                    1 child:
                    0x4200090 (has no name): ()  1x19+0+0  +976+234
              0x420008d (has no name): ()  8x8+0+0  +960+233
           0x420008b (has no name): ()  8x8+0+0  +959+232
           0x420007d (has no name): ()  590x351+0+0  +959+232
              6 children:
              0x4200083 (has no name): ()  8x8+572+347  +1531+579
              0x4200087 (has no name): ()  179x21+0+0  +959+232
                 2 children:
                 0x4200089 (has no name): ()  85x17+2+2  +962+235
                 0x4200088 (has no name): ()  64x17+87+2  +1047+235
              0x4200085 (has no name): ()  100x18+0+0  +959+232
                 1 child:
                 0x4200086 (has no name): ()  14x4+-1+-1  +959+232
              0x4200084 (has no name): ()  8x8+0+0  +959+232
              0x4200081 (has no name): ()  590x332+0+19  +959+251
                 1 child:
                 0x4200082 (has no name): ()  14x332+-1+-1  +958+250
              0x420007e (has no name): ()  590x18+0+0  +959+232
                 2 children:
                 0x4200080 (has no name): ()  496x15+2+1  +961+233
                 0x420007f (has no name): ()  90x15+498+1  +1457+233
        0x420007a (has no name): ()  590x50+0+38  +959+181
        0x4200079 (has no name): ()  590x18+0+19  +959+162
        0x4200074 (has no name): ()  590x18+0+0  +959+143
           4 children:
           0x4200078 (has no name): ()  479x18+111+0  +1070+143
           0x4200077 (has no name): ()  36x18+74+0  +1033+143
           0x4200076 (has no name): ()  36x18+37+0  +996+143
           0x4200075 (has no name): ()  36x18+0+0  +959+143
```

这和 Windows 的传统桌面 API 的设计是[非常类似](https://learn.microsoft.com/en-us/windows/win32/learnwin32/what-is-a-window-)的。不过创建大量的小窗口需要消耗不少的系统资源，因此目前常见的现代 UI 框架，不管是在 Linux 还是在 Windows 上，都基本上抛弃了这种「万物皆窗口」的理念。

### 窗口管理器 {#window-manager}

另一点有趣的是，尽管 X 中存储了各个窗口的状态（以及它们在 Z 轴的栈式关系），但是 X 本身不会去管理这些窗口要怎么被用户移动、缩放、最大最小化等，也不会去尝试装饰窗口，它只会按照自己记录的状态把这些窗口显示出来。对于具体的窗口管理工作，X 就当起了甩手掌柜，把事情都交给了**窗口管理器**。窗口管理器是一个特殊的 X 客户端，所有我们常用的窗口功能都是由窗口管理器负责的，包括但不限于管理窗口的显示布局、窗口装饰、焦点控制、虚拟桌面等等。X 服务端允许窗口管理器捕获创建窗口的事件，并且允许窗口管理器将对应的窗口 "reparent" 到窗口管理器创建的框架窗口中，以此实现让程序窗口被窗口管理器控制、装饰的效果。

窗口管理器与 X 服务器之间的交互有一些标准规范，例如 ICCCM 与 EWMH，以减小不同的窗口管理器实现之间的混乱与不一致问题。

窗口管理器本身也是一个独立的进程，如果窗口管理器退出，那么其他的 X 客户端不会停止运行，但是你可能无法再控制它们了（例如，可能它们被别的窗口挡住了，而没有窗口管理器的装饰的话，你可能没有办法移动它们）。这种分离的设计也帮助孕育了很多独特的窗口管理器设计，例如平铺式窗口管理器（例如 i3wm），相比于传统的浮动式窗口管理器，可以自动以不重叠的方式显示当前的所有窗口，用户不需要再用鼠标手动调整每个窗口的大小等等。

### 输入 {#x-input}

#### 输入设备 {#x-input-devices}

Linux 的输入子系统暴露的设备在 `/dev/input` 中，用户空间可以打开设备文件以读取输入设备的信息。可以通过 `evtest` 工具来查看输入设备的事件：

```console
$ sudo evtest
No device specified, trying to scan all of /dev/input/event*
Available devices:
（省略）
Select the device event number [0-17]: 7
（选择鼠标设备，省略）
Testing ... (interrupt to exit)
Event: time 1760901205.303790, type 2 (EV_REL), code 0 (REL_X), value -1
Event: time 1760901205.303790, -------------- SYN_REPORT ------------
Event: time 1760901205.343787, type 2 (EV_REL), code 0 (REL_X), value 1
Event: time 1760901205.343787, -------------- SYN_REPORT ------------
Event: time 1760901205.363788, type 2 (EV_REL), code 0 (REL_X), value 1
Event: time 1760901205.363788, -------------- SYN_REPORT ------------
（省略接下来鼠标移动的事件）
```

在较早的 Xorg 实现中，X server 会使用 evdev 驱动（xf86-input-evdev）直接读取 `/dev/input` 中的设备文件以获取输入事件，但是目前绝大部分情况下，evdev 驱动已经不再使用，X server 通过 libinput（xf86-input-libinput）来处理输入设备。libinput 是一个通用的输入处理库，由它解析输入事件后再传递给 X server。

libinput 则可以通过 `libinput list-devices` 来查看；`libinput` 程序还支持类似 `evtest` 的实时事件查看功能，可以使用 `libinput debug-events` 来查看输入事件：

```console
$ sudo libinput list-devices
Device:                  Power Button
Kernel:                  /dev/input/event1
Id:                      host:0000:0001
Group:                   1
Seat:                    seat0, default
Capabilities:            keyboard 
（以下省略）
$ sudo libinput debug-events /dev/input/event7
-event7   DEVICE_ADDED                 Logitech G304                     seat0 default group1  cap:kp left scroll-nat scroll-button
 event7   POINTER_MOTION               +0.000s	  0.30/  0.00 ( +1.00/ +0.00)
 event7   POINTER_MOTION            2  +0.003s	  1.81/  0.00 ( +2.00/ +0.00)
 event7   POINTER_MOTION            3  +0.007s	  2.22/  0.00 ( +2.00/ +0.00)
```

而如果要确认 X server 识别到了哪些输入设备，可以使用 `xinput` 工具。由于 `xinput` 是和 X server（而不是和设备文件）交互，因此不需要特权。以下是在 Xwayland 下执行的结果：

```console
$ xinput list
WARNING: running xinput against an Xwayland server. See the xinput man page for details.
⎡ Virtual core pointer                    	id=2	[master pointer  (3)]
⎜   ↳ Virtual core XTEST pointer              	id=4	[slave  pointer  (2)]
⎜   ↳ xwayland-pointer:16                     	id=6	[slave  pointer  (2)]
⎜   ↳ xwayland-relative-pointer:16            	id=7	[slave  pointer  (2)]
⎜   ↳ xwayland-pointer-gestures:16            	id=8	[slave  pointer  (2)]
⎣ Virtual core keyboard                   	id=3	[master keyboard (2)]
    ↳ Virtual core XTEST keyboard             	id=5	[slave  keyboard (3)]
    ↳ xwayland-keyboard:16                    	id=9	[slave  keyboard (3)]
```

#### 输入法 {#x-input-method}

最早期的 X 设计上完全没有考虑输入法的问题。然而在东亚语言（中文、日文、韩文，CJK）场景下，输入法是正常使用桌面的必需组件。因此 X 在 1994 年尝试设计了被称为 [XIM（X Input Method）](https://www.x.org/releases/X11R7.6/doc/libX11/specs/XIM/xim.html)的输入法框架，但是这一套框架逐渐无法满足现代 UI 框架与输入法的需求。因此目前在 X 上，主流的 [IBus](https://github.com/ibus/ibus) 与 [Fcitx](https://fcitx-im.org/)（包括 Fcitx 4 与 Fcitx 5）均使用另一种方案：在 GTK 或 Qt 这样的图形库中直接集成输入法支持，而不再使用 XIM。GTK 或 Qt 会直接调用输入法模块，模块内会通过 DBus 与输入法进程通信，实现功能。

这也是在做输入法配置时经常提到需要修改环境变量的原因。以 Fcitx 5 为例，通常需要设置以下环境变量：

```shell
XMODIFIERS="@im=fcitx"
GTK_IM_MODULE="fcitx"
QT_IM_MODULE="fcitx"
```

如果应用程序不使用 GTK 或 Qt，那么就会回退到 XIM 方案，即 `XMODIFIERS` 环境变量指定的输入法。

### 输出 {#x-output}

在早期，显卡只做一件事情：把帧缓冲区（framebuffer）的内容输出到显示器上。此时，显存就是一段内存空间，修改内容，显示器上对应的像素就会变化。帧缓冲区在 Linux 上暴露为 `/dev/fb0` 这样的设备文件，用户空间程序可以直接打开并且修改它的内容以读取分辨率等信息，并改变显示器上的内容。此时，X server 使用 `fbdev`（xf86-video-fbdev）驱动来操作帧缓冲区。

!!! lab "尝试直接与 `/dev/fb0` 交互，在 TTY 中输出图片"

    尝试搜索资料，写一个程序，打开 `/dev/fb0`，并使用 `ioctl` 读取必要的信息，然后 `mmap` 映射帧缓冲区后，将你想显示的图片数据写入对应的内存区域。

但是之后，显示加速的需求越来越大，显卡厂商之间设计的差异也越来越大，`fbdev` 已经不够用了。之后出现的一种解决方案是：编写 X 的输出驱动，直接操作 `/dev/mem`，通过物理地址访问显存，从而实现对显卡的控制。但是这种设计有很多问题：X 需要用 root 权限运行；如果 X 崩溃了，那么显卡的状态很可能也会坏掉；X 与 OpenGL 之间的协作也有不少问题。

因此内核提供了 DRM（Direct Rendering Manager）子系统来统一管理显卡资源，并且因此 GPU 驱动被分为了两部分：一部分在内核空间的 DRM 中（Kernel Mode Driver，KMD），另一部分在用户空间实现（User Mode Driver，UMD），很大程度缓解了所有显卡的东西都挤在 X 里面的混乱局面。你可以在 `/dev/dri` 中看到你的显卡的设备文件，一般分为主设备（`card0`）和渲染设备（`renderD128`），后者只能做渲染操作，防止将不必要的显卡配置的权限暴露给低权限图形应用。

此外，你可能还会经常看到 KMS（Kernel Mode Setting）这个词。KMS 是 DRM 的子模块，负责设置显示模式，这也将 X 从设置显示模式的负担上解放出来，并且帮助实现更平滑的显示切换（例如从 TTY 切换到 X）。

最后回到显示加速上。目前开源驱动一般的做法是：KMS 来设置显示模式，由开源的 Mesa UMD 来具体实现 OpenGL、Vulkan 等图形 API 的功能。X server 就使用 modesetting（xf86-video-modesetting）驱动，不再需要关心显卡的具体实现细节了。但是如果你是 NVIDIA 官方驱动（或者其他小众显卡厂商的闭源驱动）的用户，那么很不幸，你还是需要使用对应厂商提供的专有 X 驱动来获得显示加速。

### 混成器 {#x-compositor}

进入二十一世纪之后，桌面环境开始追求更炫酷的视觉效果，例如圆角的窗口、半透明的窗口、有阴影的窗口、不规则形状的窗口、动画效果等等。但是 X 传统仍然假设：窗口是个不透明矩形，X 服务器需要直接把这样的窗口画到屏幕上，并且跳过被挡住的部分——而且这个过程没有缓冲，动画只能靠窗口不停重绘自己来实现，非常不流畅。而混成器做的事情就是：接管图形显示的流程，让窗口不再直接画在屏幕上，而是画在一个缓冲区中，然后由混成器统一将这些缓冲区合成（composite）到屏幕上。这样一来，要显示什么酷炫的效果就由混成器说了算了。在 X 下，混成器需要调用 [X Composite 扩展](https://freedesktop.org/wiki/Software/CompositeExt/)来实现。

!!! tip "我的 X 服务器开启了哪些扩展？"

    可以使用 `xdpyinfo` 来查看当前 X 服务器开启了哪些扩展：

    ```console
    $ xdpyinfo
    （省略）
    number of extensions:    25
        BIG-REQUESTS
        Composite
        DAMAGE
        DOUBLE-BUFFER
    （省略）
    ```

最著名的例子是 compiz，它实现了很多诸如 3D 立方体桌面切换等等的效果，是 2010 年前后 Linux 桌面炫酷效果的代名词，在当时也吸引了很多用户来使用 Linux 桌面。各个桌面环境的窗口管理器，例如 GNOME 的 mutter、KDE 的 kwin 也都集成了混成器的功能。

![Compiz Cube](../images/Compiz-fusion_effects_Cube.jpg)

2007 年的 Compiz 的立方体效果。[By Nicofo，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/Compiz#/media/File:Compiz-fusion_effects_Cube.jpg)。
{: .caption }

### 远程桌面访问 {#x-remote-desktop}

X 的网络透明性设计似乎使得远程桌面访问变得非常简单，似乎只需要 `ssh -X` 或者 `ssh -Y` 就可以了。但是由于 X 协议本身的设计问题，这么做的性能并不好，主要原因包括：

1. X 协议很「啰嗦」，大量的操作都需要往返通信，这导致网络延迟会被协议放大数倍，甚至十几倍。
2. 旧的 X 程序一般会调用 X 协议的接口来画线段、字体等（例如[客户端、服务端与窗口](#client-server-window)中展示的 xedit），但是绝大多数现代 UI 框架（例如 GTK、Qt）早已经不这么做了，而是直接画图给服务器。在远程环境下意味着传输大量未压缩的图像数据，网络带宽消耗大。

因此 X 的网络透明性几乎只适合在极低延迟的网络环境下使用。对于更常见的场景，根据需求不同，可以使用传统的 VNC/RDP 方案，针对游戏场景优化的 [Sunshine](https://github.com/LizardByte/Sunshine)，或者为远程协助设计的 [RustDesk](https://rustdesk.com/) 等等。类似的远程桌面方案还有很多，可以按需选择。

!!! example "SSH + VNC 的远程桌面访问方案"

    以下介绍一种常见的远程桌面访问方案：通过 SSH 隧道访问远程主机上的 VNC 服务器。只要能够建立 SSH 连接，就可以通过这种方法获取到基本的 X 桌面环境，并且用户之间互相隔离，且不需要配置防火墙，远程桌面图像也不会经手第三方。

## Wayland

## 音频服务器

## DBus
