---
icon: simple/html5
---

# 前端简介

!!! note "主要作者"

    [@tiankaima][tiankaima]

!!! warning "本文编写中"

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
