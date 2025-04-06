---
icon: material/xml
---

# 编程语言概览

!!! note "主要作者"

    [@tiankaima][tiankaima]、[@xiao-h1024][xiao-h1024]

!!! warning "本文编写中"

!!! note

    现代开发语言种类丰富、内容繁多; 部分语言也存在不少的历史遗留问题，我们无法在一篇文档中涵盖完全。
    本文将简要介绍部分编程语言的常用工具、实用技巧等。

    阅读本文档后，您应当能够知晓：

    -   语言的适用范围 (为了实现这个任务，我应该选用哪种语言)
    -   语言的特点 (特性、发展历程、社区活跃度等)
    -   如何学习这种语言 (入门文档链接、学习资源等)
    -   各个语言的常用工具 (如何使用这种语言进行开发)

    我们也会在文章的[末尾](#style-guide)给出一些编程风格指南，帮助您更好、更规范地使用这些语言。

## Shell Script

!!! comment "适用范围"

    Shell 也许是与 Linux 打交道 (日常维护、安装等) 最直接的方式。
    在此基础上逐渐发展出了需要使用变量、控制流的 Shell Script。

    <!-- TODO: require revision -->

    Shell Script 的适用范围：**自动化、不涉及核心业务的流程** (例如周期性执行的任务、编译、安装脚本) 等，通过 Shell 可以很方便的调用其他命令、批量处理文件/目录等，但是不适合编写大型程序。

!!! note "特点"

    -   作为脚本语言，Shell Script 只提供基本的变量、控制流、函数等，几乎没有面向对象的特性。
    -   Shell Script 适合处理文本、调用系统命令等，但是不适合处理复杂的数据结构。
    -   真正意义上的开箱即用，无需额外安装，因此常用在安装、编译等场景。

参考资料：

- [Linux 101/Ch06](https://101.lug.ustc.edu.cn/Ch06/)
- [The Missing Semester of Your CS Education/shell-tools](https://missing-semester-cn.github.io/2020/shell-tools/)

作为补充，可以查阅：

- [jq](https://jqlang.github.io/jq/): 用于处理 JSON 数据
- [yq](https://github.com/mikefarah/yq): 用于处理 YAML 数据

??? comment "Shell tools"

    一个常见的提升日常效率的办法是: 使用 oh-my-zsh、fzf、tmux 等工具。

## Python

!!! comment "适用范围"

    Python 的适用范围更加广泛, 常用在 Web 开发, 以及各种科学计算、数据处理、机器学习等领域。

!!! note "特点"

    - 社区生态完善，有大量的第三方库，例如 Django、Flask、numpy、pandas 等。
    - 语法简洁，易于学习，适合初学者。
    - 「年长但恰逢新春」, 即没有 C++ 那样的历史包袱，也没有新型语言那样的不稳定性、不成熟性。
    - 类型检查不严格，但是也有完整的类型检查工具 (mypy)。

参考资料：

- [Linux 101/Ch07](https://101.lug.ustc.edu.cn/Ch07/#py)
- [Python 官方文档](https://docs.python.org/zh-cn/3/)

在掌握基础的工具链、语法之后，可以从下面几个方面进一步学习：

- [FastAPI](https://fastapi.tiangolo.com/): 尝试写一个简单的 API 服务
- [Python Data Science Handbook](https://jakevdp.github.io/PythonDataScienceHandbook/): 了解 Python 在数据科学领域的应用
- [PyTorch](https://pytorch.org/tutorials/): 了解 PyTorch 的使用
- [TensorFlow](https://tensorflow.google.cn/tutorials?hl=zh-cn): 了解 TensorFlow 的使用
- [Python Cookbook](https://python3-cookbook.readthedocs.io/zh_CN/latest/): 深入了解 Python 的一些特性

在这些过程中，Python 语言本身可能不会是一个较大的障碍，但是安装、配置等方面可能存在一点障碍，以下是一些常见的问题，我们提前整理在这里：

- [Python 3.12 importlib](https://docs.python.org/3/whatsnew/3.12.html#importlib): 导致了部分库历史版本的兼容问题 (例如 `numpy~=1.23`), 如果需要对应包的历史版本，可能需要降级 Python (或者指定 `python310` / 使用 conda 等)
- [Poetry Pytorch](https://github.com/python-poetry/poetry/issues/4231): Poetry 与 Pytorch 的兼容问题，可能需要手动安装 Pytorch

## Golang

<!-- 不熟，谁来写 -->

## HTML/CSS/JavaScript

!!! comment "适用范围"

    HTML/CSS/JavaScript 分别负责网页的结构、样式和交互。得益于 NodeJS 等技术的发展，JavaScript 不必受限在浏览器中运行，应用场景更加广泛。

    使用场景：Web 开发、跨平台应用开发等。

!!! note "特点"

    -   较完善的社区生态：有大量的库、脚手架、模板等。
    -   JavaScript 存在太多语言特性的问题，例如 [equality](https://dorey.github.io/JavaScript-Equality-Table/), [this](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Operators/this) 等。

参考资料：

- [MDN Web Docs](https://developer.mozilla.org/zh-CN/docs/Web): 百科全书

常用工具：

- 作为 JavaScript 的替代品，TypeScript 提供了静态类型检查、更好的 OOP 支持，范型、装饰器，更好的 ECMAScript 特性支持
    - 伴随着这些特性，一般而言，IDE 支持也更加友好。
    - TypeScript 一般作为 npm 脚手架使用，在编译期转为无类型检查的 JavaScript。
- SCSS: 一个 CSS 预处理器，提供了变量、嵌套、混合等功能，可以提高 CSS 的可维护性。
- Webpack: 一个模块打包工具，可以将多个 JavaScript 文件打包成一个文件，提高页面加载速度。

常用框架：

- 前端开发
    - [React](https://react.dev/): 一个用于构建用户界面的 JavaScript 库
    - [Vue](https://cn.vuejs.org/): 一套用于构建用户界面的渐进式框架
- 跨平台应用开发
    - [Electron](https://www.electronjs.org/): 使用 Web 技术构建跨平台桌面应用
    - [React Native](https://reactnative.dev/): 使用 React 构建原生应用，主要用于移动端开发

## C/C++

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

!!! comment "@xiao-h1024: 关于 C/C++ 生态的吐槽"

    C/C++ 的生态非常分散且混乱，你可以看到各种各样的构建工具，每个都声称自己解决了先前构建工具的问题，然而现实是各有各的坑点，生态还是那样混乱。想要把第三方库顺利集成到自己的项目中，还要跨平台，解决构建问题的时间都够写好多代码了，这可真是噩梦。所以还得是 Rust（逃

## 开发指南

### Style Guide {#style-guide}

- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [Style Guide for Python Code](https://peps.python.org/pep-0008/)

### Flame Graph {#flame-graph}

TBC

### IDE {#ide}

- [Visual Studio Code](https://code.visualstudio.com/): 其实 Visual Studio Code 是个代码编辑器，但是在众多插件的帮助下，可以有 IDE 一样的体验。Visual Studio Code 可以用于各种语言的开发，更是拥有非常出色的远程开发功能。
- [Pycharm](https://www.jetbrains.com/pycharm/): Jetbrains 开发的 Python IDE，提供了开箱即用的 Python 开发体验，支持 Python 的各种框架
- [Clion](https://www.jetbrains.com/clion/): Jetbrains 开发的 C++ IDE，使用 CMake 管理工程，拥有强大的静态检查功能，以及强大的代码重构功能
- [QT Creator](https://www.qt.io/zh-cn/product/development-tools): 主要用于开发 Qt 应用的 IDE
- [Cursor](https://www.cursor.com/): 深度集成了 AI 工具的代码编辑器，基于 Visual Studio Code 开发，兼容大部分 Visual Studio Code 的插件，Tab 键的体验谁用谁知道！

### 其他工具

#### 网络抓包

TBC
