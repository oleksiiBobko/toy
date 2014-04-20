---
layout: post
title:  "Microkernel is all we need"
---
As I wrote in the previous post I've come to a conclusion that single address space is not an option. Each domain should occupy its own address space. In addition such design will give Toy OS potential ability to support POSIX applications. I prefer the modern *microkernel* design. So I plan to start working on microkernel soon.

Miscellaneous design points
---------------------------
<p>

* **L4-like microkernel.** The original L4 design is very good, but I believe some design modification will be required to (e.g. to support persistence).

* **Support for small and large pages.** For each address space there should be a corresponding page size. Small pages are good for tiny non-persistent processes (and maybe for kernel address space, not sure here). Large pages are good for persistent domains (they use large portions of address space so otherwise page tables will consume too big amount of non-paged RAM).

* **No third party code in kernel.** The kernel should be very small and efficient. Only simple predictable algorithms. Thus there is no need for neither C++ exceptions nor standard headers.
