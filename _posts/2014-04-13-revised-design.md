---
layout: post
title:  "Revised design"
---
Before starting to deepen in a next iteration of coding I decided to review my previous architectural design. There are my previous design points:

* **Single 64-bit address space.** This will give ability for applications to call kernel without need to switch context and serialize data. Moreover it will shorten thread context switches and will remove need to clear TLB-cache.

* **Virtual machine for applications.** It will disable applications to exceed own memory boundaries (memory protection). Virtual machine is also useful for distributed environments with several CPU architectures.

* **Storage devices are mapped to address space.** RAM is just caching access to persistent storage via address space. In-use pages are loaded to RAM, and not-in-use ones are saved back to device. This is done transparently to applications. This approach makes files redundant: regularly allocated memory is already persistent, thus there is no need to save its content to files.

* **Persistent applications.** They survive both system restart and moving to another machine. This is partially achieved by the previous point as well as by absence of resource descriptors (e.g. no file handles). To use any resource a unique identifier must be used instead (no need to open the resource before the actual usage). Оn the one hand this will expose some additional overhead (but not too drastic because of caching) but on the other hand this will detach such call from place and time constraints (code which is resumed after system restart or moved to another machine will be able to continue running).

Domains
-------
Storage devices are mounted on a single 64-bit address space. Each device takes some contiguous region (let's call it *domain*). It is possible to mount a storage device on arbitrary address (in case if there is enough unoccupied place).

![single 64-bit address space](/toy/files/2014-04/single-64bit-address-space.png)

After mounting domain threads resume running. The cheapest function calls are calls inside a domain. They impose no additional overhead than regular C-functions. Inter-domain calls (including kernel calls) are not so cheap (e.g. need to handle caller/callee domain unmount during the call). Still there is no need to serialize in/out data (single address space).

This will not work
--------------------
As for me the scheme above is very beautiful. Unfortunately it has a hidden defect which make it impossible. There is no simple way to make domain code *position independent (PIC)*. It's needed to enable mounting on arbitrary address (otherwise there's no guarantee that two given drives could be mounted simultaneously - their addresses could overlap).

Yes, there are useful techniques and tricks which are widely used in shared libraries. But they don't work for living code (code which is unloaded and reloaded again). Think about allocating memory. You call *malloc* and save the returned memory address to some variable. Now the domain gets unmounted and remounted on a different address. Here the code operates absolute addresses so the techniques based on instruction pointer offsets are not working.

The x86_64 could help us here, because of its *segmentation* capability. Indeed we could dynamically create memory segment for domain we're going to mount. All domain code addresses are absolute, starting from its beginning. They are implicitly incremented by the segment address inside CPU. But:

* Inter-domain calls must be performed using *far pointers* (segment + offset). Intra-domain calls should use regular *near pointers* (far pointers are expensive and bloat binary code). Two different types of pointers is not a good idea.
* Far pointers are not part of the C/C++ standards and not supported by the major compilers (e.g. gcc or clang).
* OS design based segmentation is not portable to CPU architectures other than x86.

<p>
Conclusion
----------
The multiple address spaces scheme is unavoidable. Persistence mechanism must be built on top of it. Each domain should occupy its own address space.

**P.S.** *I've been reminded of lack of segmentation support in x86_64 (unlike x86), so all the far pointers stuff mentioned above is not relevant.*
