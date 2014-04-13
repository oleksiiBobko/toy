---
layout: post
title:  "Starting a new iteration (ver.0.4)"
---

It's been 9 months since I worked last time on the previous iteration of *Toy OS* (ver.0.3). Now I feel it's time to start a next one. Let's enumerate the main accomplishments of each previous version:

+ **ver.0.1** - long mode booting, interrupts, memory mapping, CPU-topology
+ **ver.0.2** - multiboot support, SMP, thread scheduling, mutex, PCI detection
+ **ver.0.3** - code portability, sleep

In ver.0.4 I would like to reconsider all my previous approaches from ground up. By now there are number of decisions I should remade:

+ Should I use a modern build system (maybe, a Python-based one) instead of Make? (*yes*)
+ Should I start supporting multiple platforms from this iteration? (*no*)
+ Should I support UEFI2 instead of multiboot support? (*no*)
+ Should I redesign basic architecture by adding support for multiple address spaces? (*no*)
+ Should I use C++11 instead of C99? (*yes*)

Let's review all these questions one by one.

## Choosing a build system

I already thought about replacing ugly *GNU Make* with something pretty, modern and Python-based. There are two such build systems: *Scons* and *Waf*. First is more popular but the second is cleaner, faster and more pythonic. I personally prefer the second one. But both are not really suitable for osdev. They have prebuilt compile and build templates (command line parameters) which are suitable for client applications but not for kernels. This means I have to do some hacking which will demand a deeper knowledge about the chosen build system. I really was not happy with this fact (here GNU Make is more convenient!) and even wrote a little module for that (see [tbs.py](/toy/files/2014-03/tbs.py) and [build.py](/toy/files/2014-03/build.py)). Now I believe that handmade solution is not an option (hard to support and scale), so I'll try to deepen my Waf knowledge. Will try it again. If I will not succeed, I'll return to GNU Make.

## Multiple platform support

In ver.0.3 I split all my code into platform-dependent and platform-independent parts. But such division cannot be precise enough when you have a single platform. You just cannot test your decisions. So it is important to start developing for several platforms from ground up. There are only two actual platforms to target Toy OS: *x86\_64* and *AArch64*. But the second is still very recent, so I neither have stable tools nor published tutorials to start from. Unfortunately I should stick with x86\_64 in this iteration.

## UEFI2 vs. Multiboot

As I know that AArch64 devices will support UEFI2 as well as some newer x86\_64 machines. So it seems reasonable to stick with it. On the other hand I read that GRUB2 is already ported to both x86\_64's UEFI2 and AArch64. Because Multiboot specification is much simpler than UEFI2 I prefer to stay with it (at least for ver.0.4).

## Single vs. Multiple address spaces

Current design implies a single address space in combination with virtual machine which will enforce memory safety for client applications. This means that unmanaged applications (as well as legacy C/C++ code) will be able to crash the whole system. For practical purposes it would be useful to support multiple address spaces to give ability to safely run ported C/C++ applications. But such support complicates simplicity of the original design (every object is identified just by its pointer, no need for serialization, fast context switches, etc.). Not now, at least not in ver.0.4.

## C++11 vs. C99

No doubt that C++ is much more powerful language. Yes, it is bloated and overcomplicated, but it is well supported, has good compilers as well as the nice recent standard. I cannot avoid C++ because of existing code base which is very useful. For example I will need LLVM for my virtual machine implementation. If I cannot reject implementing C++ standard library, it's worth to employ powerful C++ features inside kernel. So I'll try to use some kind of C/C++ combination.
