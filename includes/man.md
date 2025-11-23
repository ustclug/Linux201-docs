<!--
  Links to man pages

  See <https://squidfunk.github.io/mkdocs-material/reference/tooltips/#adding-a-glossary> for how this file is used.
-->

<!-- markdownlint-disable-file MD041 MD053 -->

<!-- man 1 -->

[git-bisect.1]: https://git-scm.com/docs/git-bisect
[git-fetch.1]: https://git-scm.com/docs/git-fetch
[perf-stat.1]: https://man7.org/linux/man-pages/man1/perf-stat.1.html
[rrsync.1]: https://man7.org/linux/man-pages/man1/rrsync.1.html
[rsync.1]: https://man7.org/linux/man-pages/man1/rsync.1.html
[sacctmgr.1]: https://slurm.schedmd.com/sacctmgr.html
[scrun.1]: https://slurm.schedmd.com/scrun.html
[ssh-keygen.1]: https://man7.org/linux/man-pages/man1/ssh-keygen.1.html
[systemd-run.1]: https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html
[tigervncserver.1]: https://manpages.debian.org/unstable/tigervnc-standalone-server/tigervncserver.1.en.html
[vncconfig.1]: https://linux.die.net/man/1/vncconfig
[xserver.1]: https://linux.die.net/man/1/xserver

<!-- man 2 -->

[mlock.2]: https://man7.org/linux/man-pages/man2/mlock.2.html
[pivot_root.2]: https://man7.org/linux/man-pages/man2/pivot_root.2.html

<!-- man 3 -->

[getaddrinfo.3]: https://man7.org/linux/man-pages/man3/getaddrinfo.3.html

<!-- man 4 -->

[md.4]: https://man7.org/linux/man-pages/man4/md.4.html

<!-- man 5 -->

[adduser.conf.5]: https://manpages.debian.org/stable/adduser/adduser.conf.5.en.html
[apt.conf.5]: https://manpages.debian.org/unstable/apt/apt.conf.5.en.html
[apt_preferences.5]: https://manpages.debian.org/unstable/apt/apt_preferences.5.en.html
[deluser.conf.5]: https://manpages.debian.org/stable/adduser/deluser.conf.5.en.html
[fstab.5]: https://man7.org/linux/man-pages/man5/fstab.5.html
[journald.conf.5]: https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html
[sd_notify.3]: https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html
<!-- begin slurm config files -->
[slurm.conf.5]: https://slurm.schedmd.com/slurm.conf.html
[slurmdbd.conf.5]: https://slurm.schedmd.com/slurmdbd.conf.html
[cgroup.conf.5]: https://slurm.schedmd.com/cgroup.conf.html
[slurmdbd.conf.5]: https://slurm.schedmd.com/slurmdbd.conf.html
[gres.conf.5]: https://slurm.schedmd.com/gres.conf.html
[oci.conf.5]: https://slurm.schedmd.com/oci.conf.html
<!-- end slurm config files -->
[smartd.conf.5]: https://linux.die.net/man/5/smartd.conf
[ssh_config.5]: https://man.openbsd.org/ssh_config
[sshd_config.5]: https://man.openbsd.org/sshd_config
[systemd.exec.5]: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html
[systemd.exec.5#Environment]: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#Environment
[systemd.exec.5#Sandboxing]: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#Sandboxing
[systemd.kill.5]: https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html
[systemd.resource-control.5]: https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html
[systemd.service.5]: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
[systemd.service.5#Restart=]: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#Restart=
[systemd.timer.5]: https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html
[systemd.unit.5]: https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html
[user@.service.5]: https://www.freedesktop.org/software/systemd/man/latest/user@.service.html

<!-- man 7 -->

[apt-patterns.7]: https://manpages.debian.org/unstable/apt/apt-patterns.7.en.html
[capabilities.7]: https://man7.org/linux/man-pages/man7/capabilities.7.html
[cgroups.7]: https://man7.org/linux/man-pages/man7/cgroups.7.html
[icmp.7]: https://man7.org/linux/man-pages/man7/icmp.7.html
[namespaces.7]: https://man7.org/linux/man-pages/man7/namespaces.7.html
[pcap-filter.7]: https://www.tcpdump.org/manpages/pcap-filter.7.html
[zfsprops.7]: https://openzfs.github.io/openzfs-docs/man/master/7/zfsprops.7.html

<!-- man 8 -->

<!-- Note: Debian man pages for useradd(8)/userdel(8) mentions the "low-level" feature and recommends adduser(8)/deluser(8) instead. 
Do not link to a "generic" man page for these commands -->
[adduser.8]: https://manpages.debian.org/stable/adduser/adduser.8.en.html
<!-- None of Debian, man7.org or linux.die.net provides conntrack(8), weird -->
[conntrack.8]: https://man.archlinux.org/man/conntrack.8.en
[deluser.8]: https://manpages.debian.org/stable/adduser/deluser.8.en.html
[iptables.8]: https://www.man7.org/linux/man-pages/man8/iptables.8.html
[iptables-extensions.8]: https://www.man7.org/linux/man-pages/man8/iptables-extensions.8.html
[logrotate.8]: https://linux.die.net/man/8/logrotate
[mount.8]: https://man7.org/linux/man-pages/man8/mount.8.html
[sg_unmap.8]: https://linux.die.net/man/8/sg_unmap
[sg_write_same.8]: https://linux.die.net/man/8/sg_write_same
[smartctl.8]: https://linux.die.net/man/8/smartctl
[sshd.8]: https://linux.die.net/man/8/sshd
<!-- begin slurm daemons -->
[sackd.8]: https://slurm.schedmd.com/sackd.html
[slurmctld.8]: https://slurm.schedmd.com/slurmctld.html
[slurmd.8]: https://slurm.schedmd.com/slurmd.html
[slurmdbd.8]: https://slurm.schedmd.com/slurmdbd.html
[slurmrestd.8]: https://slurm.schedmd.com/slurmrestd.html
<!-- end slurm daemons -->
[systemd-logind.8]: https://www.freedesktop.org/software/systemd/man/latest/systemd-logind.html
[useradd.8]: https://manpages.debian.org/stable/passwd/useradd.8.en.html
[userdel.8]: https://manpages.debian.org/stable/passwd/userdel.8.en.html
[xfs_growfs.8]: https://linux.die.net/man/8/xfs_growfs
[zfs-receive.8]: https://openzfs.github.io/openzfs-docs/man/master/8/zfs-receive.8.html
[zfs-send.8]: https://openzfs.github.io/openzfs-docs/man/master/8/zfs-send.8.html
