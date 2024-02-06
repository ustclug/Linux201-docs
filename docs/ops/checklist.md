# 运维检查单

## 远程管理

- 如果物理服务器带有 IPMI 等带外管理功能，是否已启用并配置了固定 IP 地址和安全的密码？

## 系统安全

- 是否所有用户都（或者至少 root 及有 sudo 权限的用户）具有强密码？
- SSH 的密码登录是否已禁用？（`PasswordAuthentication no`）
    - 如果有任何原因需要启用密码登录，是否已禁用 root 用户的密码登录？（`PermitRootLogin prohibit-password`）
    - 或者，仅对有需要的用户启用密码登录？（`Match User <username>`、`PasswordAuthentication yes`）

## 网络安全

- MySQL、PostgreSQL、Redis 等数据库服务是否只监听了本地地址？
    - 或者，已经配置了外部防火墙阻断相关端口的入站连接？（MySQL: 3306，PostgreSQL: 5432，Redis: 6379）
