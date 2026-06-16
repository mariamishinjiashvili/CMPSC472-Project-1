# CMPSC 472 - Project 1: MapReduce Parallel Computing

## Overview

This project implements two MapReduce-style systems in C to demonstrate operating system concepts such as multithreading, multiprocessing, inter-process communication (IPC), and synchronization.

The project consists of two parts:

* **Part 1:** Parallel sorting using Merge Sort
* **Part 2:** Maximum-value aggregation with constrained shared memory

Both parts include thread-based and process-based implementations and compare their performance using different numbers of workers.

## Features

* POSIX thread implementation
* Process-based implementation using `fork()`
* Shared memory communication
* POSIX semaphores and mutex synchronization
* Merge Sort for parallel sorting
* Parallel maximum-value computation
* Performance benchmarking with varying worker counts

## Technologies Used

* C
* POSIX Threads (pthreads)
* POSIX Semaphores
* Shared Memory
* Pipes
* Merge Sort
* Linux

## Running the Project

Compile the program using GCC:

```bash
gcc -pthread -o project project.c
```

Run the executable:

```bash
./project
```

To test different scenarios, modify the input array size in the source code and rerun the program.

## Performance Evaluation

The project compares execution time and memory usage for:

* 1 worker
* 2 workers
* 4 workers
* 8 workers

Experiments were performed on arrays of size 32 and 131,072 to evaluate the trade-offs between multithreading and multiprocessing.

## Key Takeaways

* Multithreading performs better for small workloads due to lower overhead and shared memory access.
* Multiprocessing can outperform multithreading on larger workloads by reducing contention and utilizing multiple CPU cores.
* Proper synchronization with mutexes and semaphores is essential to prevent race conditions and ensure correctness.

## Author

Mariami Shinjiashvili

Penn State University
B.S. Computer Science
