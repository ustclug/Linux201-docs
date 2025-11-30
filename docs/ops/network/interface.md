---
icon: material/link-box
---

# 网络接口

!!! warning "本文编写中"

本章介绍 Linux 系统中的各种虚拟网络接口类型及其配置方法。

## 桥接 {#bridge}

!!! question "桥不就是一个交换机吗？"

    是的，尽管「桥接」指的是将网口加入到一个虚拟交换机中，但在 Linux 中，桥接接口（bridge interface）除了这个虚拟交换机之外，也包含了一根由本机接入该交换机的虚拟接口。
    因此 bridge interface 上可以配置 IP 地址，本机也可以通过该接口进行通信。

!!! question "为什么 IP 地址要配置在桥接接口上，而不是被桥接的网口上？"

    这是因为被桥接的网口已经失去了上层的功能，所有从该网口接收到的数据包都会直接转交给桥接接口处理，而不会再经过网口本身的协议栈。

    具体来说，在将网口加入桥接的时候，bridge 模块会将 [`br_handle_frame` 函数][br_handle_frame] 注册为该网口的 `rx_handler` 回调函数中，从而接管该网口的所有入向数据包处理逻辑。
    在处理完接收的数据包后，`br_handle_frame` 会返回 `RX_HANDLER_CONSUMED`，表示该数据包已经被 bridge 处理完毕，不再在网口本身的协议栈中继续处理。
    因此，即使你再在网口上配置 IP 地址等信息，这些信息也不会被使用到。

    类似地，由于每个网口的 `rx_handler` 是唯一的，因此在网口被加入桥接后，就无法再注册其他的 `rx_handler` 回调函数了，例如加入另一个桥或引申出 MACVLAN 接口等。
    此处唯一的例外是 802.1Q VLAN 接口，因为 VLAN 子接口并不通过 `rx_handler` 机制实现。

  [br_handle_frame]: https://elixir.bootlin.com/linux/v6.17.8/source/net/bridge/br_input.c#L331

### Veth 对 {#veth-pair}

## 网卡聚合 {#bonding}

## MACVLAN 与 IPVLAN {#macvlan-ipvlan}

## VRF {#vrf}
