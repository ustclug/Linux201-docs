---
icon: simple/cplusplus
---

# C/C++ 与构建工具

!!! note "主要作者"

    [@xiao-h1024][xiao-h1024]

!!! warning "本文编写中"

!!! comment "适用范围"

    C/C++ 的适用范围非常广泛，几乎可以适用于计算机的各种领域，通常用于性能要求较高或是资源受限、贴近底层的地方，比如操作系统内核、游戏引擎、高频量化交易、嵌入式开发等

!!! note "特点"

    - 高性能：编译为机器码，没有额外开销
    - 手动内存管理：与一些自带 GC 的语言不同，C/C++ 要求开发者自行管理内存
    - 生态分散：C/C++ 并没有官方的包管理器，生态较为分散，现有的包管理器、构建工具并不完善

参考资料：

- [Linux 101/Ch07](https://101.lug.ustc.edu.cn/Ch07/#c)
- [C++ Reference](https://en.cppreference.com/w/)
- [CppCon](https://cppcon.org/)
- [Modern C++ Programming](https://federico-busato.github.io/Modern-CPP-Programming/)

常用工具：

- [CMake](https://cmake.org/): 目前最流行的跨平台 C/C++ 构建系统
- [Meson](https://mesonbuild.com): 一种开源构建系统，比 CMake 更加用户友好
- [Xmake](https://xmake.io): 现代化的 C/C++ 构建工具，拥有快速构建、生成工程文件、包管理等强大功能，同时轻量易上手
- [Vcpkg](https://vcpkg.io): 微软开发的免费开源 C/C++ 包管理器，可以跨平台，能够与 CMake 等构建工具协作
- [Conan](https://conan.io/): 另一个 C/C++ 的包管理器，比 Vcpkg 更方便定制

Style Guide:

- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)

!!! comment "@xiao-h1024: 关于 C/C++ 生态的吐槽"

    C/C++ 的生态非常分散且混乱，你可以看到各种各样的构建工具，每个都声称自己解决了先前构建工具的问题，然而现实是各有各的坑点，生态还是那样混乱。想要把第三方库顺利集成到自己的项目中，还要跨平台，解决构建问题的时间都够写好多代码了，这可真是噩梦。所以还得是 Rust（逃
