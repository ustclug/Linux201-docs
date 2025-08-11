---
icon: simple/python
---

# Python

!!! note "主要作者"

    [@tiankaima][tiankaima]

!!! warning "本文编写中"

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

Style Guide:

- [Style Guide for Python Code](https://peps.python.org/pep-0008/)

在掌握基础的工具链、语法之后，可以从下面几个方面进一步学习：

- [FastAPI](https://fastapi.tiangolo.com/): 尝试写一个简单的 API 服务
- [Python Data Science Handbook](https://jakevdp.github.io/PythonDataScienceHandbook/): 了解 Python 在数据科学领域的应用
- [PyTorch](https://pytorch.org/tutorials/): 了解 PyTorch 的使用
- [TensorFlow](https://tensorflow.google.cn/tutorials?hl=zh-cn): 了解 TensorFlow 的使用
- [Python Cookbook](https://python3-cookbook.readthedocs.io/zh_CN/latest/): 深入了解 Python 的一些特性

在这些过程中，Python 语言本身可能不会是一个较大的障碍，但是安装、配置等方面可能存在一点障碍，以下是一些常见的问题，我们提前整理在这里：

- [Python 3.12 importlib](https://docs.python.org/3/whatsnew/3.12.html#importlib): 导致了部分库历史版本的兼容问题 (例如 `numpy~=1.23`), 如果需要对应包的历史版本，可能需要降级 Python (或者指定 `python310` / 使用 conda 等)
- [Poetry Pytorch](https://github.com/python-poetry/poetry/issues/4231): Poetry 与 Pytorch 的兼容问题，可能需要手动安装 Pytorch
