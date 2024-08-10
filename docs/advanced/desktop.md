---
icon: octicons/device-desktop-16
---

# Linux 桌面与窗口系统

!!! warning "本文初稿编写中"

相比于久负盛名的 Windows 与 macOS，Linux 的桌面以及其生态是独特的。本文将简单介绍 Linux 桌面与窗口系统中一些重要的概念。

## X

X 窗口系统起源于 1984 年。在这个时代，桌面环境没有酷炫的效果，相比之下，性能与资源占用重要得多。并且当时个人计算机还是一个新兴的概念，用户更多的时候需要使用终端机连接到服务器上运行任务。因此，X 的设计上包含了当时那个年代设计的局限性，并且有着独特的「网络透明性」的设计：需要显示窗口的程序（客户端）和可以给用户显示窗口的程序（服务端）是可以分离的，通过网络去连接。

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

## Wayland

## DBus
