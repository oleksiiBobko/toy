---
layout: post
title:  "Restarted with AArch64 (ver.0.4)"
---

It's been 6 months since I wrote the last post. My design vision was vacillated between single and multiple address spaces. In the last case we should use microkernel. For now I continue sticking to single address space. I believe there will be no considerable performance impact due to several causes:

1. No need for serialization, fast context switches, etc.
2. User-level compiler will perform sophisticated static analysis which will ensure memory safety (being inspired by Rust language now I tend to refuse virtual machine in favour of native compiler).

Still we'll have a problem with buggy third-party C/C++ code. So inserting it will require some dedicated permission.

Last week I did significant progress with AArch64 bootstrap code (latest versions of GCC/CLang and QEMU now support it). By now I have a minimal kernel with logging capability (restricted printf-like version).

Next days I'll adopt x86\_64 code from ver.0.3 to the current sources. I decided to implement each feature both for AArch64 and x86\_64 before moving to a next one.

Interrupts will be the next milestone. For AArch64 I need to figure out how to enable timer and how start other logical CPUs. This will allow to write a thread scheduler.